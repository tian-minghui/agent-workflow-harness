from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from agent_workflow_harness import gates
from agent_workflow_harness.storage import atomic_write_text
from agent_workflow_harness.task import Task
from agent_workflow_harness.tokens import TemplateError, substitute_template, template_variables
from agent_workflow_harness.workflow import (
    Condition,
    Gate,
    Producer,
    Step,
    replace_step_templates,
    Workflow,
    WorkflowError,
    Transition,
    has_control_characters,
)

ANCHOR_SCHEMA = "agent-workflow-harness.task-anchor.v1"
TASK_STATE_SCHEMA = "agent-workflow-harness.task-state.v2"
ALIAS_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
TASK_ID_PATTERN = re.compile(r"^task-[a-f0-9]{32}$")
FINGERPRINT_PATTERN = re.compile(r"^[a-f0-9]{64}$")
START_VARIABLE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
START_VARIABLE_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")
TASK_TITLE_PATTERN = re.compile(r"^[A-Za-z0-9 -]{5,120}$")
TASK_TITLE_ALPHANUMERIC_PATTERN = re.compile(r"[A-Za-z0-9]")
POINTER_FIELDS = {"schema", "task_id", "workflow_alias", "title"}
STATE_FIELDS = {
    "schema",
    "task_id",
    "workflow_alias",
    "title",
    "step",
    "workflow_dir",
    "artifact_dir",
    "workflow_yaml_sha256",
    "inputs",
    "facts",
    "visited_steps",
    "backedge_counts",
}
BACKEDGE_LIMIT = 3


class WorkflowCommandError(RuntimeError):
    """Raised when a workflow command cannot be evaluated."""

    def __init__(
        self,
        reason: str,
        hint: str | None = None,
        status: str = "error",
        active_task_title: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.hint = hint
        self.status = status
        self.active_task_title = active_task_title


@dataclass(frozen=True)
class TaskContext:
    id: str
    title: str
    step: str
    artifact_dir: str

    @property
    def payload(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "step": self.step,
            "artifactDir": self.artifact_dir,
        }


@dataclass(frozen=True)
class StartResult:
    status: str
    task: TaskContext
    instruction: str

    @property
    def title(self) -> str:
        return self.task.title


@dataclass(frozen=True)
class NextResult:
    status: str
    task: TaskContext
    instruction: str
    gate: str | None = None
    reason: str | None = None

    @property
    def title(self) -> str:
        return self.task.title


@dataclass
class ActiveTask:
    pointer_path: Path
    pointer: dict[str, object]
    task_dir: Path
    task: Task
    state: dict[str, object]
    workflow_dir: Path
    workflow: Workflow

    @property
    def title(self) -> str:
        return str(self.state["title"])

    @property
    def current_step(self) -> str:
        return str(self.state["step"])

    @property
    def artifact_dir(self) -> str:
        return str(self.state["artifact_dir"])

    @property
    def task_context(self) -> TaskContext:
        return TaskContext(
            id=str(self.state["task_id"]),
            title=self.title,
            step=self.current_step,
            artifact_dir=self.artifact_dir,
        )

    def _template_context(self) -> dict[str, str]:
        inputs = self.state["inputs"]
        return template_variables(
            workflow_dir=self.workflow_dir,
            task_dir=self.artifact_dir,
            inputs=inputs,
        )

    def resolved_step(self, name: str) -> Step:
        return _resolve_step(self.workflow.step(name), self._template_context())


@dataclass(frozen=True)
class ResolvedCondition:
    value: bool | str
    source: str
    fact: dict[str, object] | None = None


def resolve_project_directory(project_path: str | None = None) -> Path:
    if project_path:
        return Path(project_path).expanduser().resolve()
    env_override = os.environ.get("AWH_PROJECT_DIR")
    if env_override:
        return Path(env_override).expanduser().resolve()

    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip()).resolve()
    return Path.cwd().resolve()


def normalize_title(title: str) -> str:
    return " ".join(title.strip().split())


def _is_valid_task_title(value: str) -> bool:
    return (
        TASK_TITLE_PATTERN.fullmatch(value) is not None
        and TASK_TITLE_ALPHANUMERIC_PATTERN.search(value) is not None
    )


def _task_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:64]


def _task_artifact_dir(title: str, task_id: str) -> str:
    return (
        ".workflow-harness/task-artifacts/"
        f"{_task_slug(title)}-{task_id}"
    )


def validate_title(title: str) -> str:
    if "\n" in title or "\r" in title or not _is_valid_task_title(normalize_title(title)):
        raise WorkflowCommandError(
            "Task title must be a natural English line of 5 to 120 ASCII letters, digits, spaces, and hyphens",
            "Use a concise English task title such as Implement user profile export",
        )
    return normalize_title(title)


def validate_alias(alias: str) -> str:
    if ALIAS_PATTERN.fullmatch(alias) is None:
        raise WorkflowCommandError(
            "Workflow aliases must use letters, digits, dots, underscores, or hyphens",
            "Run awh start <workflow-alias> --task <title>",
        )
    return alias


def parse_start_variables(raw_variables: list[str]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for raw_variable in raw_variables:
        try:
            name, value = raw_variable.split("=", 1)
        except ValueError as error:
            raise WorkflowCommandError(
                "Start variable must use name=value",
                "Run awh start <alias> --task <title> --var name=value",
            ) from error
        if START_VARIABLE_NAME_PATTERN.fullmatch(name) is None:
            raise WorkflowCommandError(
                "Start variable names must use lowercase snake_case",
                "Use a lowercase snake_case name without spaces or quotes",
            )
        if len(value) > 256:
            raise WorkflowCommandError(
                "Start variable values must be one token of at most 256 characters",
                "Use a workflow producer for complex judgment",
            )
        if START_VARIABLE_VALUE_PATTERN.fullmatch(value) is None:
            raise WorkflowCommandError(
                "Start variable values must be one nonempty token",
                "Use a single token and derive complex judgment with a workflow producer",
            )
        if name in variables:
            raise WorkflowCommandError(f"Duplicate start variable: {name}")
        variables[name] = value
    return variables


def resolve_source_package(alias: str, project: Path) -> Path | None:
    project_package = project / ".agents" / "workflows" / alias
    if (project_package / "workflow.yaml").is_file():
        return project_package

    user_package = Path.home() / ".agents" / "workflows" / alias
    if (user_package / "workflow.yaml").is_file():
        return user_package

    builtin_package = Path(__file__).parent / "workflows" / alias
    if (builtin_package / "workflow.yaml").is_file():
        return builtin_package
    return None


def _runtime_directory(project: Path) -> Path:
    return project / ".workflow-harness"


def _definition_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_task_id(value: object, reason: str) -> str:
    if not isinstance(value, str) or TASK_ID_PATTERN.fullmatch(value) is None:
        raise WorkflowCommandError(reason)
    return value


def _read_json(path: Path, reason: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowCommandError(reason) from error
    if not isinstance(value, dict):
        raise WorkflowCommandError(reason)
    return value


def _validate_pointer(pointer: dict[str, object]) -> None:
    if set(pointer) != POINTER_FIELDS or pointer.get("schema") != ANCHOR_SCHEMA:
        raise WorkflowCommandError("Active workflow task pointer is invalid or unreadable")
    _validate_task_id(pointer.get("task_id"), "Active workflow task pointer is invalid or unreadable")
    if not isinstance(pointer.get("workflow_alias"), str) or not pointer["workflow_alias"]:
        raise WorkflowCommandError("Active workflow task pointer is invalid or unreadable")
    title = pointer.get("title")
    if not isinstance(title, str) or not _is_valid_task_title(title):
        raise WorkflowCommandError("Active workflow task pointer is invalid or unreadable")


def _validate_state(state: dict[str, object]) -> None:
    if state.get("schema") == "agent-workflow-harness.task-state.v1":
        raise WorkflowCommandError(
            "Active workflow v1 state is not supported",
            "Inspect retained evidence and start a replacement v2 task",
        )
    if set(state) != STATE_FIELDS or state.get("schema") != TASK_STATE_SCHEMA:
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    task_id = _validate_task_id(
        state.get("task_id"), "Active workflow task state is invalid or unreadable"
    )
    for field in ("workflow_alias", "title", "step", "workflow_dir"):
        if not isinstance(state.get(field), str) or not state[field]:
            raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    title = str(state["title"])
    if not _is_valid_task_title(title):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    artifact_dir = state.get("artifact_dir")
    if (
        not isinstance(artifact_dir, str)
        or not artifact_dir
        or artifact_dir != _task_artifact_dir(title, task_id)
    ):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    fingerprint = state.get("workflow_yaml_sha256")
    if (
        not isinstance(fingerprint, str)
        or FINGERPRINT_PATTERN.fullmatch(fingerprint) is None
    ):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    if not Path(str(state["workflow_dir"])).is_absolute():
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")

    inputs = state.get("inputs")
    if not isinstance(inputs, dict) or any(
        not isinstance(key, str)
        or not isinstance(value, str)
        or len(value) > 256
        or START_VARIABLE_NAME_PATTERN.fullmatch(key) is None
        or START_VARIABLE_VALUE_PATTERN.fullmatch(value) is None
        for key, value in inputs.items()
    ):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")

    facts = state.get("facts")
    if not isinstance(facts, dict):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    for fact_name, fact in facts.items():
        if not isinstance(fact_name, str) or START_VARIABLE_NAME_PATTERN.fullmatch(fact_name) is None:
            raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
        if not isinstance(fact, dict) or set(fact) != {"value", "producing_step", "producer_type", "producer_ref"}:
            raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
        fact_value = fact.get("value")
        if isinstance(fact_value, bool):
            valid_fact_value = True
        elif isinstance(fact_value, str):
            valid_fact_value = (
                bool(fact_value)
                and len(fact_value) <= 256
                and START_VARIABLE_VALUE_PATTERN.fullmatch(fact_value) is not None
            )
        else:
            valid_fact_value = False
        if (
            not valid_fact_value
            or not isinstance(fact.get("producing_step"), str)
            or not fact.get("producing_step")
            or fact.get("producer_type") not in {"workflow_script", "command"}
            or not isinstance(fact.get("producer_ref"), str)
            or not fact.get("producer_ref")
        ):
            raise WorkflowCommandError("Active workflow task state is invalid or unreadable")

    visited = state.get("visited_steps")
    if (
        not isinstance(visited, list)
        or any(not isinstance(value, str) for value in visited)
        or len(visited) != len(set(visited))
    ):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")

    backedges = state.get("backedge_counts")
    if not isinstance(backedges, dict):
        raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
    for source, targets in backedges.items():
        if not isinstance(source, str) or not isinstance(targets, dict):
            raise WorkflowCommandError("Active workflow task state is invalid or unreadable")
        for target, count in targets.items():
            if (
                not isinstance(target, str)
                or not isinstance(count, int)
                or isinstance(count, bool)
                or not 1 <= count <= BACKEDGE_LIMIT
            ):
                raise WorkflowCommandError("Active workflow task state is invalid or unreadable")


def _append_task_error_once(task_dir: Path, reason: str) -> None:
    """Record an integrity failure in an already-located task without masking the CLI error."""
    try:
        Task(task_dir).append_history_once({"event": "error", "reason": reason})
    except (OSError, TypeError):
        return


def _load_pointer(pointer_path: Path) -> dict[str, object]:
    pointer = _read_json(pointer_path, "Active workflow task pointer is invalid or unreadable")
    _validate_pointer(pointer)
    return pointer


def _append_source_drift(
    task: Task,
    state: dict[str, object],
    current_fingerprint: str,
) -> None:
    task.append_history_once(
        {
            "event": "workflow_source_changed",
            "step": state.get("step"),
            "recorded_workflow_yaml_sha256": state.get("workflow_yaml_sha256"),
            "current_workflow_yaml_sha256": current_fingerprint,
        }
    )


def _raise_source_drift(task: Task, state: dict[str, object]) -> None:
    workflow_path = Path(str(state["workflow_dir"])) / "workflow.yaml"
    try:
        current_fingerprint = _definition_fingerprint(workflow_path)
    except OSError:
        task.append_history_once(
            {
                "event": "workflow_source_changed",
                "step": state.get("step"),
                "recorded_workflow_yaml_sha256": state.get("workflow_yaml_sha256"),
                "current_workflow_yaml_sha256": None,
            }
        )
        raise WorkflowCommandError(
            "Workflow definition source is unavailable for the active task",
            "Restart the task with an available workflow source package",
        ) from None

    if current_fingerprint != state.get("workflow_yaml_sha256"):
        _append_source_drift(task, state, current_fingerprint)
        raise WorkflowCommandError(
            "Workflow definition source changed during the active task",
            "Restart the workflow task to bind the updated definition",
        )


def _load_validated_task_identity(
    project: Path,
) -> tuple[dict[str, object], dict[str, object], Task]:
    pointer_path = _runtime_directory(project) / "task.json"
    if not pointer_path.is_file():
        raise WorkflowCommandError(
            "No active workflow task",
            "Run awh start <workflow-alias> --task <title>",
        )

    pointer = _load_pointer(pointer_path)
    task_id = _validate_task_id(
        pointer.get("task_id"),
        "Active workflow task pointer is invalid or unreadable",
    )
    task_dir = _runtime_directory(project) / "tasks" / task_id
    if not task_dir.is_dir() or not (task_dir / "state.json").is_file():
        if task_dir.is_dir():
            _append_task_error_once(
                task_dir,
                "Active workflow task state is missing or unreadable",
            )
        raise WorkflowCommandError(
            "Active workflow task directory is missing",
            "Fix the project runtime state or restart the workflow task",
        )

    state_reason = "Active workflow task state is invalid or unreadable"
    try:
        state = _read_json(task_dir / "state.json", state_reason)
        _validate_state(state)
    except WorkflowCommandError as error:
        _append_task_error_once(task_dir, error.reason)
        raise

    artifact_path = Path(str(state["artifact_dir"]))
    if not (project / artifact_path).is_dir():
        _append_task_error_once(task_dir, "Active workflow task artifact directory is missing")
        raise WorkflowCommandError(
            "Active workflow task artifact directory is missing",
            "Fix the project runtime state or restart the workflow task",
        )

    if (
        state.get("task_id") != pointer.get("task_id")
        or state.get("workflow_alias") != pointer.get("workflow_alias")
        or state.get("title") != pointer.get("title")
        or task_dir.name != state.get("task_id")
    ):
        _append_task_error_once(
            task_dir,
            "Active workflow task identity mismatch",
        )
        raise WorkflowCommandError(
            "Active workflow task identity mismatch",
            "Fix the runtime pointer and state pair or restart the workflow task",
        )

    return pointer, state, Task(task_dir)


def _load_bound_workflow(task_dir: Path, state: dict[str, object]) -> Workflow:
    workflow_path = Path(str(state["workflow_dir"])) / "workflow.yaml"
    try:
        workflow = Workflow.from_yaml(workflow_path)
    except WorkflowError as error:
        _append_task_error_once(
            task_dir,
            "Active workflow definition is invalid or unreadable",
        )
        raise WorkflowCommandError(
            "Active workflow definition is invalid or unreadable"
        ) from error
    if state.get("step") not in workflow.steps:
        _append_task_error_once(
            task_dir,
            "Active workflow task step is invalid or unreadable",
        )
        raise WorkflowCommandError(
            "Active workflow task state is invalid or unreadable"
        )
    return workflow


def _load_active_task(
    project: Path,
    *,
    verify_source: bool = True,
) -> ActiveTask:
    pointer, state, task = _load_validated_task_identity(project)
    if verify_source:
        _raise_source_drift(task, state)
    workflow = _load_bound_workflow(task.root, state)
    return ActiveTask(
        pointer_path=_runtime_directory(project) / "task.json",
        pointer=pointer,
        task_dir=task.root,
        task=task,
        state=state,
        workflow_dir=Path(str(state["workflow_dir"])),
        workflow=workflow,
    )


def _replace_template(value: str, variables: dict[str, str], field: str) -> str:
    try:
        return substitute_template(value, variables)
    except TemplateError as error:
        raise WorkflowCommandError(
            f"Workflow template is invalid: {field}: {error}",
            "Fix the workflow template variable and restart the workflow task",
        ) from error


def _resolve_step(step: Step, variables: dict[str, str]) -> Step:
    try:
        return replace_step_templates(
            step,
            lambda value, field: _replace_template(value, variables, field),
        )
    except TemplateError as error:
        raise WorkflowCommandError(
            f"Workflow template is invalid: {error}",
            "Fix the workflow template variable and restart the workflow task",
        ) from error


def _instruction(step: Step) -> str:
    guide = step.guide
    if not isinstance(guide, str):
        raise WorkflowCommandError(
            "Workflow task has no active instruction",
            "Inspect the active workflow package or choose another workflow",
        )
    return guide


def _human_gate(step) -> Gate | None:
    matches = [gate for gate in step.gates if gate.type == "human"]
    if len(matches) > 1:
        raise WorkflowCommandError("A step can contain at most one human gate")
    return matches[0] if matches else None


def _hash_field(digest, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def _human_evidence_fingerprint(project: Path, gate) -> str:
    digest = hashlib.sha256()
    for evidence_path in gate.evidence:
        source = project / evidence_path
        if not source.is_file():
            raise WorkflowCommandError(
                f"Human evidence is missing: {evidence_path}",
                "Create the declared evidence file before recording a human decision",
            )
        _hash_field(digest, evidence_path.encode("utf-8"))
        _hash_field(digest, source.read_bytes())
    return digest.hexdigest()


def _human_context(gate) -> tuple[str, str]:
    request = " ".join((gate.request or "").split())
    evidence = ", ".join(gate.evidence)
    return request, evidence


def _human_command_hint() -> str:
    return '确认请运行 awh approve；拒绝请运行 awh reject --reason "..."。'


def _human_missing_reason(gate, missing_paths) -> str:
    request, _ = _human_context(gate)
    evidence = ", ".join(missing_paths)
    return (
        f"HUMAN_REVIEW_PENDING: 请确认 {request}。"
        f"请先创建证据文件：{evidence}，再进行人审。"
    )


def _human_pending_reason(gate, prior_reason: str | None = None) -> str:
    request, evidence = _human_context(gate)
    reason = f"HUMAN_REVIEW_PENDING: 请确认 {request}。"
    if prior_reason:
        reason += f" 上一次反馈：{prior_reason}。"
    reason += f" 请查看 {evidence}。"
    return reason + _human_command_hint()


def _human_unchanged_reason(gate, reason: str) -> str:
    request, evidence = _human_context(gate)
    normalized_reason = " ".join(reason.split())
    return (
        f"HUMAN_REVIEW_UNCHANGED: 上一次拒绝仍然适用：{normalized_reason}。"
        f"请确认 {request}。请查看 {evidence}。"
        + _human_command_hint()
    )


def _human_rejected_reason(gate, reason: str) -> str:
    request, evidence = _human_context(gate)
    normalized_reason = " ".join(reason.split())
    return (
        f"HUMAN_REVIEW_REJECTED: {normalized_reason}。"
        f"请确认 {request}。请查看 {evidence}。"
        + _human_command_hint()
    )


def _human_stale_reason(gate) -> str:
    request, evidence = _human_context(gate)
    return (
        f"HUMAN_APPROVAL_STALE: 已确认的 {evidence} 发生变化。"
        f"请确认 {request}。请查看 {evidence}。"
        + _human_command_hint()
    )


def _terminal_context(active: ActiveTask) -> TaskContext:
    return TaskContext(
        id=str(active.state["task_id"]),
        title=active.title,
        step=active.workflow.terminal,
        artifact_dir=active.artifact_dir,
    )


def _human_block(
    task: Task,
    step_name: str,
    human_gate: Gate,
    reason: str,
    instruction: str,
    task_context: TaskContext,
) -> NextResult:
    task.append_history(
        {
            "event": "blocked",
            "step": step_name,
            "gate": human_gate.id,
            "reason": reason,
        }
    )
    return NextResult("blocked", task_context, instruction, human_gate.id, reason)


def _finish_active_task(active: ActiveTask) -> NextResult:
    active.task.append_history_once(
        {"event": "done", "step": active.workflow.terminal}
    )
    active.pointer_path.unlink(missing_ok=True)
    return NextResult("done", _terminal_context(active), "")


def _project_arguments(producer: Producer, project: Path) -> list[str]:
    return [
        value if value.startswith("-") else str(project / value)
        for value in producer.project_args
    ]


def _run_producer(
    producer: Producer,
    step_name: str,
    project: Path,
    workflow_dir: Path,
    timeout: int,
) -> ResolvedCondition:
    provenance = {
        "value": True,
        "producing_step": step_name,
        "producer_type": producer.type,
        "producer_ref": producer.script or producer.command or "",
    }
    try:
        if producer.type == "workflow_script":
            script_path = workflow_dir / str(producer.script)
            if not script_path.is_file():
                raise WorkflowCommandError(f"Condition producer is missing: {producer.variable}")
            completed = subprocess.run(
                [sys.executable, str(script_path), *_project_arguments(producer, project)],
                cwd=project,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout,
            )
            if completed.returncode != 0:
                raise WorkflowCommandError(
                    f"Condition producer failed for {producer.variable}"
                )
            scalar = completed.stdout.strip()
            if not scalar or "\n" in scalar or "\r" in scalar or has_control_characters(scalar):
                raise WorkflowCommandError(
                    f"Condition producer {producer.variable} must emit one scalar line"
                )
            value: bool | str
            if scalar in {"true", "false"}:
                value = scalar == "true"
            else:
                value = scalar
        else:
            completed = subprocess.run(
                producer.command or "",
                cwd=project,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout,
            )
            if completed.returncode == 1:
                value = False
            elif completed.returncode == 0:
                value = True
            else:
                raise WorkflowCommandError(
                    f"Condition producer failed for {producer.variable}"
                )
    except subprocess.TimeoutExpired as error:
        raise WorkflowCommandError(
            f"Condition producer timed out for {producer.variable}"
        ) from error
    except OSError as error:
        raise WorkflowCommandError(
            f"Condition producer failed for {producer.variable}"
        ) from error

    provenance["value"] = value
    return ResolvedCondition(value=value, source="producer", fact=dict(provenance))


def _resolve_condition(
    variable: str,
    active: ActiveTask,
    project: Path,
    step: Step,
) -> ResolvedCondition:
    producer = next(
        (candidate for candidate in step.producers if candidate.variable == variable),
        None,
    )
    if producer is not None:
        return _run_producer(
            producer,
            active.current_step,
            project,
            active.workflow_dir,
            active.workflow.producer_timeout_seconds,
        )

    facts = active.state["facts"]
    if variable in facts:
        fact = facts[variable]
        return ResolvedCondition(value=fact["value"], source="runtime_fact", fact=dict(fact))

    inputs = active.state["inputs"]
    if variable in inputs:
        return ResolvedCondition(value=inputs[variable], source="start_input")

    alias = f"WF_{variable.upper()}"
    value = os.environ.get(alias)
    if isinstance(value, str):
        return ResolvedCondition(value=value, source="environment")

    raise WorkflowCommandError(f"Condition variable is unresolved: {variable}")


def _condition_satisfied(value: bool | str, condition: Condition) -> bool:
    if condition.literal_type is bool:
        if isinstance(value, bool):
            normalized = value
        elif value in {"true", "false"}:
            normalized = value == "true"
        else:
            normalized = False
        return normalized is (condition.literal == "true")
    return isinstance(value, str) and value == condition.literal


def _route_error(reason: str, hint: str | None = None) -> None:
    raise WorkflowCommandError(reason, hint, status="error")


def _select_route(
    active: ActiveTask,
    project: Path,
    step: Step,
) -> tuple[Transition, dict[str, ResolvedCondition], str | None, int | None]:
    variables = sorted(
        {
            transition.condition.variable
            for transition in step.transitions
            if transition.condition is not None
        }
    )
    resolved = {
        variable: _resolve_condition(variable, active, project, step)
        for variable in variables
    }
    conditional_matches = [
        transition
        for transition in step.transitions
        if transition.condition is not None
        and _condition_satisfied(
            resolved[transition.condition.variable].value,
            transition.condition,
        )
    ]
    if len(conditional_matches) > 1:
        _route_error(
            f"Step {step.name} has multiple matching condition routes"
        )

    if conditional_matches:
        selected = conditional_matches[0]
        condition_variable = selected.condition.variable if selected.condition else None
        selected_source = resolved[condition_variable].source if condition_variable else None
        selected_value = resolved[condition_variable].value if condition_variable else None
    else:
        defaults = [transition for transition in step.transitions if transition.default]
        if not defaults:
            _route_error(f"Step {step.name} has no matching conditional route or default route")
        selected = defaults[0]
        condition_variable = None
        selected_source = None
        selected_value = None

    visited = list(active.state["visited_steps"])
    backedge_count: int | None = None
    if selected.to_step in visited:
        source_counts = active.state["backedge_counts"].get(step.name, {})
        previous = int(source_counts.get(selected.to_step, 0))
        if previous >= BACKEDGE_LIMIT:
            _route_error(
                f"Backedge {step.name} -> {selected.to_step} reached its three-use limit",
                "Inspect the route evidence and start a replacement task or revise the workflow",
            )
        backedge_count = previous + 1

    selected_backedge = (
        {"source": step.name, "target": selected.to_step}
        if selected.to_step in visited
        else None
    )
    return selected, resolved, selected_backedge, backedge_count


def run_next(project_path: str | None = None) -> NextResult:
    project = resolve_project_directory(project_path)
    active = _load_active_task(project)
    current_step_name = active.current_step
    step = active.resolved_step(current_step_name)
    if current_step_name == active.workflow.terminal:
        return _finish_active_task(active)

    failed_gate = gates.evaluate(step, project, active.workflow_dir)
    if failed_gate is not None:
        active.task.append_history(
            {
                "event": "blocked",
                "step": current_step_name,
                "gate": failed_gate.gate_id,
                "reason": failed_gate.reason,
            }
        )
        return NextResult(
            "blocked",
            active.task_context,
            _instruction(step),
            failed_gate.gate_id,
            failed_gate.reason,
        )

    human_gate = _human_gate(step)
    human_decision_metadata: dict[str, object] = {}
    if human_gate is not None:
        latest_decision = active.task.latest_human_decision(current_step_name, human_gate.id)
        missing_evidence = [
            evidence_path
            for evidence_path in human_gate.evidence
            if not (project / evidence_path).is_file()
        ]
        if missing_evidence:
            if latest_decision is not None and latest_decision.get("decision") == "approved":
                failed_reason = _human_stale_reason(human_gate)
            else:
                failed_reason = _human_missing_reason(human_gate, missing_evidence)
            return _human_block(
                active.task,
                current_step_name,
                human_gate,
                failed_reason,
                _instruction(step),
                active.task_context,
            )

        current_fingerprint = _human_evidence_fingerprint(project, human_gate)
        if latest_decision is None:
            failed_reason = _human_pending_reason(human_gate)
            return _human_block(
                active.task,
                current_step_name,
                human_gate,
                failed_reason,
                _instruction(step),
                active.task_context,
            )

        decision = str(latest_decision.get("decision", ""))
        recorded_fingerprint = str(latest_decision.get("evidence_fingerprint", ""))
        feedback = str(latest_decision.get("reason", "") or latest_decision.get("note", ""))

        if decision == "rejected":
            if current_fingerprint == recorded_fingerprint:
                failed_reason = _human_unchanged_reason(human_gate, feedback)
            else:
                failed_reason = _human_pending_reason(human_gate, feedback)
            return _human_block(
                active.task,
                current_step_name,
                human_gate,
                failed_reason,
                _instruction(step),
                active.task_context,
            )

        if current_fingerprint != recorded_fingerprint:
            failed_reason = _human_stale_reason(human_gate)
            return _human_block(
                active.task,
                current_step_name,
                human_gate,
                failed_reason,
                _instruction(step),
                active.task_context,
            )

        if decision != "approved":
            failed_reason = _human_pending_reason(human_gate, feedback)
            return _human_block(
                active.task,
                current_step_name,
                human_gate,
                failed_reason,
                _instruction(step),
                active.task_context,
            )

        human_decision_metadata = {
            "human_gate": human_gate.id,
            "human_decision": decision,
            "human_decision_fingerprint": recorded_fingerprint,
        }

    transition, resolved, backedge_identity, backedge_count = _select_route(
        active, project, step
    )
    condition_variable = (
        transition.condition.variable
        if transition.condition is not None
        else None
    )
    resolved_condition = resolved.get(condition_variable) if condition_variable else None

    new_state = json.loads(json.dumps(active.state))
    for variable, resolved_value in resolved.items():
        if resolved_value.fact is not None:
            new_state["facts"][variable] = resolved_value.fact
    new_state["step"] = transition.to_step
    if transition.to_step not in new_state["visited_steps"]:
        new_state["visited_steps"].append(transition.to_step)
    if backedge_identity is not None:
        source = str(backedge_identity["source"])
        target = str(backedge_identity["target"])
        source_counts = new_state["backedge_counts"].setdefault(source, {})
        source_counts[target] = backedge_count
    _write_state(active.task.state_file, new_state)

    success_event: dict[str, object] = {
        "event": "success",
        "from_step": current_step_name,
        "to_step": transition.to_step,
    }
    if transition.condition is not None and resolved_condition is not None:
        success_event.update(
            {
                "condition_variable": transition.condition.variable,
                "condition_value": resolved_condition.value,
                "resolve_source": resolved_condition.source,
            }
        )
    if backedge_identity is not None:
        success_event["backedge"] = dict(backedge_identity)
        success_event["backedge_count"] = backedge_count
    success_event.update(human_decision_metadata)
    active.task.append_history(success_event)

    if transition.to_step == active.workflow.terminal:
        return _finish_active_task(active)

    next_step = active.resolved_step(transition.to_step)
    return NextResult(
        "active",
        TaskContext(
            id=str(active.state["task_id"]),
            title=active.title,
            step=transition.to_step,
            artifact_dir=active.artifact_dir,
        ),
        _instruction(next_step),
    )


def record_human_decision(
    project_path: str | None,
    decision: str,
    decision_payload: str | None = None,
    *,
    advance: bool = False,
) -> NextResult:
    """Record an approval or rejection for the active stage without advancing."""
    if decision not in {"approved", "rejected"}:
        raise WorkflowCommandError("Human decision is invalid")

    project = resolve_project_directory(project_path)
    active = _load_active_task(project, verify_source=False)
    current_step_name = active.current_step
    step = active.resolved_step(current_step_name)

    human_gate = _human_gate(step)
    if human_gate is None:
        raise WorkflowCommandError(
            "This stage has no human gate",
            "Run awh next to continue the workflow",
        )

    failed_gate = gates.evaluate(step, project, active.workflow_dir)
    if failed_gate is not None:
        raise WorkflowCommandError(
            "Human review requires all automatic gates to pass first",
            f"Fix automatic gate {failed_gate.gate_id} and try again",
        )

    fingerprint = _human_evidence_fingerprint(project, human_gate)
    latest_decision = active.task.latest_human_decision(current_step_name, human_gate.id)
    if (
        decision == "approved"
        and latest_decision is not None
        and latest_decision.get("decision") == "rejected"
        and latest_decision.get("evidence_fingerprint") == fingerprint
    ):
        raise WorkflowCommandError(
            "Unchanged rejected evidence cannot be approved",
            "Modify the evidence and request a new human review",
        )

    normalized_payload = " ".join((decision_payload or "").split())
    if len(normalized_payload) > 500:
        raise WorkflowCommandError(
            "Human decision payload is too long",
            "Use a concise reason or note of at most 500 characters",
        )
    if has_control_characters(normalized_payload):
        raise WorkflowCommandError(
            "Human decision payload contains invalid control characters",
            "Remove control characters and try again",
        )

    if decision == "rejected":
        if not normalized_payload:
            raise WorkflowCommandError("Rejection reason is required")
        record_payload: dict[str, object] = {"reason": normalized_payload}
    else:
        record_payload = {"note": normalized_payload} if normalized_payload else {}

    event: dict[str, object] = {
        "event": "human_decision",
        "step": current_step_name,
        "gate": human_gate.id,
        "decision": decision,
        "evidence_fingerprint": fingerprint,
    }
    event.update(record_payload)
    active.task.append_history(event)

    if decision == "approved" and advance:
        return run_next(project)

    request, evidence = _human_context(human_gate)
    if decision == "rejected":
        response_reason = _human_rejected_reason(
            human_gate, str(record_payload.get("reason", ""))
        )
    else:
        response_reason = (
            f"HUMAN_REVIEW_RECORDED: 请确认 {request}。请查看 {evidence}。"
            "已记录 approved。请继续运行 awh next。"
        )
    return NextResult(
        status="blocked",
        task=active.task_context,
        instruction=_instruction(step),
        gate=human_gate.id,
        reason=response_reason,
    )


def _write_state(path: Path, state: dict[str, object]) -> None:
    atomic_write_text(
        path,
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
    )


def _create_pointer_once(path: Path, pointer: dict[str, object]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    atomic_write_text(
        temporary,
        json.dumps(pointer, ensure_ascii=False, indent=2) + "\n",
    )
    try:
        os.link(temporary, path)
    except FileExistsError:
        temporary.unlink(missing_ok=True)
        return False
    temporary.unlink(missing_ok=True)
    return True


def validate_workflow_definition(alias_str: str, project_path: str | None = None) -> tuple[str, str | None]:
    alias = validate_alias(alias_str)
    project = resolve_project_directory(project_path)
    source_package = resolve_source_package(alias, project)
    if source_package is None:
        raise WorkflowCommandError(f"Workflow alias not found: {alias}")
    try:
        Workflow.from_yaml(source_package / "workflow.yaml")
    except WorkflowError as error:
        raise WorkflowCommandError(str(error), status="invalid") from None
    return alias, str(source_package)


def _require_workflow_template_variables(
    workflow: Workflow,
    variables: dict[str, str],
) -> None:
    missing = sorted(workflow.template_references() - set(variables))
    if missing:
        raise WorkflowCommandError(
            f"Workflow start inputs are unresolved: {', '.join(missing)}",
            "Pass every referenced variable with awh start --var name=value",
        )
    try:
        for step in workflow.steps.values():
            _resolve_step(step, variables)
    except WorkflowCommandError as error:
        raise WorkflowCommandError(
            error.reason,
            "Revise the workflow template variables and retry awh start",
        ) from error


def start_workflow(
    alias_str: str,
    raw_title: str,
    project_path: str | None = None,
    raw_variables: list[str] | None = None,
) -> StartResult:
    alias = validate_alias(alias_str)
    title = validate_title(raw_title)
    variables = parse_start_variables(raw_variables or [])
    project = resolve_project_directory(project_path)
    runtime_dir = _runtime_directory(project)
    pointer_path = runtime_dir / "task.json"

    if pointer_path.exists():
        pointer, state, task = _load_validated_task_identity(project)
        existing_title = normalize_title(str(pointer["title"]))
        if pointer.get("workflow_alias") != alias or existing_title != title:
            raise WorkflowCommandError(
                "Project already has an active workflow task",
                "Use awh next to continue the active task, or confirm a replacement with the user",
                status="conflict",
                active_task_title=existing_title,
            )
        if variables and state.get("inputs") != variables:
            raise WorkflowCommandError(
                "Active task start inputs cannot be changed",
                "Run awh next, omit --var, or repeat the exact task inputs",
                status="conflict",
                active_task_title=existing_title,
            )

        _raise_source_drift(task, state)
        workflow = _load_bound_workflow(task.root, state)
        context = template_variables(
            workflow_dir=Path(str(state["workflow_dir"])),
            task_dir=str(state["artifact_dir"]),
            inputs=state["inputs"],
        )
        step = _resolve_step(workflow.step(str(state["step"])), context)
        return StartResult(
            "active",
            TaskContext(
                id=str(state["task_id"]),
                title=str(state["title"]),
                step=str(state["step"]),
                artifact_dir=str(state["artifact_dir"]),
            ),
            _instruction(step),
        )

    source_package = resolve_source_package(alias, project)
    if source_package is None:
        raise WorkflowCommandError(
            f"Workflow alias not found: {alias}",
            "Run awh start <workflow-alias> --task <title>",
        )

    workflow_path = source_package / "workflow.yaml"
    try:
        definition_fingerprint = _definition_fingerprint(workflow_path)
        workflow = Workflow.from_yaml(workflow_path)
    except WorkflowError as error:
        raise WorkflowCommandError(
            "Workflow definition is invalid or incomplete",
            "Fix the workflow definition or choose another alias",
        ) from error
    except OSError as error:
        raise WorkflowCommandError(
            "Workflow definition could not be read",
            "Fix the workflow definition or choose another alias",
        ) from error

    task_id = f"task-{uuid.uuid4().hex}"
    artifact_dir = _task_artifact_dir(title, task_id)
    context = template_variables(
        workflow_dir=source_package.resolve(),
        task_dir=artifact_dir,
        inputs=variables,
    )
    _require_workflow_template_variables(workflow, context)

    task_dir = runtime_dir / "tasks" / task_id
    artifact_path = project / artifact_dir
    try:
        task_dir.mkdir(parents=True, exist_ok=False)
        artifact_path.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        if task_dir.exists():
            shutil.rmtree(task_dir, ignore_errors=True)
        raise WorkflowCommandError(
            "Workflow task directories could not be created",
            "Fix the project directory permissions and retry awh start",
        ) from error
    source_directory = source_package.resolve()
    state = {
        "schema": TASK_STATE_SCHEMA,
        "task_id": task_id,
        "workflow_alias": alias,
        "title": title,
        "step": workflow.entry,
        "workflow_dir": str(source_directory),
        "artifact_dir": artifact_dir,
        "workflow_yaml_sha256": definition_fingerprint,
        "inputs": variables,
        "facts": {},
        "visited_steps": [workflow.entry],
        "backedge_counts": {},
    }
    _write_state(task_dir / "state.json", state)
    task = Task(task_dir)
    task.append_history(
        {
            "event": "started",
            "alias": alias,
            "title": title,
            "entry": workflow.entry,
            "workflow_dir": str(source_directory),
            "workflow_yaml_sha256": definition_fingerprint,
            "artifact_dir": artifact_dir,
            "inputs": variables,
        }
    )

    pointer = {
        "schema": ANCHOR_SCHEMA,
        "task_id": task_id,
        "workflow_alias": alias,
        "title": title,
    }
    if not _create_pointer_once(pointer_path, pointer):
        shutil.rmtree(task_dir)
        shutil.rmtree(artifact_path)
        return start_workflow(alias, title, str(project), raw_variables)

    step = _resolve_step(workflow.step(workflow.entry), context)
    return StartResult("active", TaskContext(task_id, title, workflow.entry, artifact_dir), _instruction(step))
