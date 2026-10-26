from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path
import re
from typing import Callable, Mapping

import yaml

from agent_workflow_harness.tokens import TemplateError, extract_template_references, validate_template_syntax


class WorkflowError(ValueError):
    """Raised when a workflow definition cannot be used as a state machine."""


def has_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 0x7F for character in value)


VERSION_PATTERN = re.compile(r"^v2$")
CONDITION_VARIABLE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
CONDITION_LITERAL_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")
CONDITION_PATTERN = re.compile(
    r"^([a-z][a-z0-9_]*) == ([A-Za-z0-9._/-]+)$"
)


@dataclass(frozen=True)
class Condition:
    variable: str
    literal: str
    literal_type: type[bool] | type[str]

    @classmethod
    def from_text(cls, raw: object) -> "Condition":
        if not isinstance(raw, str):
            raise WorkflowError("Workflow validation failed: a when condition must be a string")
        match = CONDITION_PATTERN.fullmatch(raw)
        if match is None:
            raise WorkflowError(f"Workflow validation failed: invalid when condition: {raw}")
        variable = match.group(1)
        literal = match.group(2)
        if CONDITION_VARIABLE_PATTERN.fullmatch(variable) is None:
            raise WorkflowError(f"Workflow validation failed: invalid condition variable: {variable}")
        if CONDITION_LITERAL_PATTERN.fullmatch(literal) is None:
            raise WorkflowError(f"Workflow validation failed: invalid condition literal: {literal}")
        if literal in {"true", "false"}:
            return cls(variable=variable, literal=literal, literal_type=bool)
        return cls(variable=variable, literal=literal, literal_type=str)

    def text(self) -> str:
        return f"{self.variable} == {self.literal}"


def _safe_script_path(
    script: object,
    entity: str,
    exception_prefix: str,
) -> str:
    if not isinstance(script, str) or not script:
        raise WorkflowError(f"Workflow validation failed: {exception_prefix} needs a script")
    script_path = Path(script)
    if script_path.is_absolute() or ".." in script_path.parts or script_path.suffix != ".py":
        message = f"Workflow validation failed: {entity} script must stay inside the workflow package"
        raise WorkflowError(message)
    return script


def _validate_templates(value: str, field: str) -> None:
    try:
        validate_template_syntax(value, field)
    except TemplateError as error:
        raise WorkflowError(f"Workflow validation failed: {error}") from error


def _safe_project_args(
    raw_project_args: object,
    entity: str,
) -> tuple[str, ...]:
    if not isinstance(raw_project_args, list) or any(
        not isinstance(arg, str) or not arg for arg in raw_project_args
    ):
        raise WorkflowError(f"Workflow validation failed: {entity} needs relative project args")
    project_args = tuple(raw_project_args)
    if any(Path(arg).is_absolute() or ".." in Path(arg).parts for arg in project_args):
        raise WorkflowError(f"Workflow validation failed: {entity} project args must stay inside the project")
    return project_args


@dataclass(frozen=True)
class Gate:
    id: str
    type: str
    path: str | None = None
    command: str | None = None
    script: str | None = None
    project_args: tuple[str, ...] = ()
    request: str | None = None
    evidence: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "Gate":
        gate_id = data.get("id")
        gate_type = data.get("type")
        if not isinstance(gate_id, str) or not gate_id.strip():
            raise WorkflowError("Workflow validation failed: every gate needs a non-empty id")
        if gate_type not in {"file_exists", "command", "workflow_script", "human"}:
            raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an unsupported type")

        if gate_type == "human":
            request = data.get("request")
            if not isinstance(request, str) or not request.strip():
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} needs a non-empty request")
            if len(request) > 300:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an oversized request")
            if has_control_characters(request):
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} has invalid control characters in its request")
            raw_evidence = data.get("evidence", [])
            _validate_templates(request, f"gate {gate_id} request")
            if not isinstance(raw_evidence, list) or not raw_evidence:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} needs non-empty evidence paths")
            if len(raw_evidence) > 5:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} has more than 5 evidence paths")
            evidence: list[str] = []
            for raw_path in raw_evidence:
                if not isinstance(raw_path, str) or not raw_path.strip():
                    raise WorkflowError(f"Workflow validation failed: gate {gate_id} needs non-empty evidence paths")
                if has_control_characters(raw_path):
                    raise WorkflowError(f"Workflow validation failed: gate {gate_id} has control characters in an evidence path")
                candidate_path = raw_path.strip()
                _validate_templates(raw_path, f"gate {gate_id} evidence path")
                if "\\" in candidate_path or re.search(r"^[A-Za-z]:", candidate_path):
                    raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an unsafe evidence path")
                path = Path(candidate_path)
                if path.is_absolute() or ".." in path.parts:
                    raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an unsafe evidence path")
                if len(candidate_path) > 100:
                    raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an oversized evidence path")
                normalized_path = path.as_posix()
                if normalized_path in evidence:
                    raise WorkflowError(f"Workflow validation failed: gate {gate_id} has duplicate evidence paths")
                evidence.append(normalized_path)
            return cls(id=gate_id, type=gate_type, request=request, evidence=tuple(evidence))

        if gate_type == "file_exists":
            path = data.get("path")
            if not isinstance(path, str) or not path:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} needs a path")
            if has_control_characters(path) or "\\" in path:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an unsafe path")
            if re.search(r"^[A-Za-z]:", path):
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an unsafe path")
            path_value = Path(path)
            _validate_templates(path, f"gate {gate_id} path")
            if path_value.is_absolute() or ".." in path_value.parts:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} has an unsafe path")
            return cls(id=gate_id, type=gate_type, path=path)

        if gate_type == "command":
            command = data.get("command")
            if not isinstance(command, str) or not command:
                raise WorkflowError(f"Workflow validation failed: gate {gate_id} needs a command")
            _validate_templates(command, f"gate {gate_id} command")
            return cls(id=gate_id, type=gate_type, command=command)

        script = _safe_script_path(data.get("script"), f"gate {gate_id}", f"gate {gate_id}")
        project_args = _safe_project_args(data.get("project_args", []), f"gate {gate_id}")
        for project_arg in project_args:
            _validate_templates(project_arg, f"gate {gate_id} project arg")
        return cls(id=gate_id, type=gate_type, script=script, project_args=project_args)


@dataclass(frozen=True)
class Producer:
    variable: str
    type: str
    script: str | None = None
    command: str | None = None
    project_args: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, variable: str, data: Mapping[str, object]) -> "Producer":
        producer_type = data.get("type")
        if producer_type not in {"workflow_script", "command"}:
            raise WorkflowError(f"Workflow validation failed: producer {variable} has an unsupported type")
        if producer_type == "command":
            command = data.get("command")
            if not isinstance(command, str) or not command:
                raise WorkflowError(f"Workflow validation failed: producer {variable} needs a command")
            _validate_templates(command, f"producer {variable} command")
            return cls(variable=variable, type=producer_type, command=command)

        script = _safe_script_path(
            data.get("script"), f"producer {variable}", f"producer {variable}"
        )
        project_args = _safe_project_args(
            data.get("project_args", []), f"producer {variable}"
        )
        for project_arg in project_args:
            _validate_templates(project_arg, f"producer {variable} project arg")
        return cls(variable=variable, type=producer_type, script=script, project_args=project_args)


@dataclass(frozen=True)
class Transition:
    from_step: str
    to_step: str
    condition: Condition | None = None
    default: bool = False

    @classmethod
    def from_mapping(cls, source: str, data: Mapping[str, object]) -> "Transition":
        if set(data) - {"to", "when", "default"}:
            raise WorkflowError(f"Workflow validation failed: step {source} has an unsupported transition field")
        target = data.get("to")
        if not isinstance(target, str) or not target:
            raise WorkflowError(f"Workflow validation failed: step {source} has a transition without a target")
        condition: Condition | None = None
        if "when" in data:
            condition = Condition.from_text(data["when"])
            if isinstance(data.get("default"), bool):
                raise WorkflowError(f"Workflow validation failed: step {source} cannot combine when and default")
        default = data.get("default")
        if default is not None and default is not True:
            raise WorkflowError(f"Workflow validation failed: step {source} has an invalid default marker")
        return cls(
            from_step=source,
            to_step=target,
            condition=condition,
            default=default is True,
        )


def replace_step_templates(
    step: "Step",
    replace_value: Callable[[str, str], str],
) -> "Step":
    """Apply one pass over every template-bearing field of a step."""

    def replaced_gate(gate: Gate) -> Gate:
        changes: dict[str, object] = {}
        if gate.path is not None:
            changes["path"] = replace_value(gate.path, f"gate {gate.id} path")
        if gate.command is not None:
            changes["command"] = replace_value(gate.command, f"gate {gate.id} command")
        if gate.request is not None:
            changes["request"] = replace_value(gate.request, f"gate {gate.id} request")
        if gate.evidence:
            changes["evidence"] = tuple(
                replace_value(evidence_path, f"gate {gate.id} evidence path")
                for evidence_path in gate.evidence
            )
        if gate.project_args:
            changes["project_args"] = tuple(
                replace_value(project_arg, f"gate {gate.id} project arg")
                for project_arg in gate.project_args
            )
        return replace(gate, **changes)

    def replaced_producer(producer: Producer) -> Producer:
        changes: dict[str, object] = {}
        if producer.command is not None:
            changes["command"] = replace_value(
                producer.command, f"producer {producer.variable} command"
            )
        if producer.project_args:
            changes["project_args"] = tuple(
                replace_value(project_arg, f"producer {producer.variable} project arg")
                for project_arg in producer.project_args
            )
        return replace(producer, **changes)

    guide = step.guide
    replaced_guide = (
        replace_value(guide, f"step {step.name} guide")
        if isinstance(guide, str)
        else guide
    )
    return replace(
        step,
        guide=replaced_guide,
        gates=tuple(replaced_gate(gate) for gate in step.gates),
        producers=tuple(replaced_producer(producer) for producer in step.producers),
    )

@dataclass(frozen=True)
class Step:
    name: str
    guide: str | None
    gates: tuple[Gate, ...]
    producers: tuple[Producer, ...] = ()
    transitions: tuple[Transition, ...] = ()

    @classmethod
    def from_mapping(cls, name: str, data: Mapping[str, object], is_terminal: bool) -> "Step":
        guide = data.get("guide")
        raw_gates = data.get("gates", [])
        if isinstance(guide, str):
            _validate_templates(guide, f"step {name} guide")
        if not isinstance(raw_gates, list):
            raise WorkflowError(f"Workflow validation failed: step {name} has non-list gates")
        gates = tuple(Gate.from_mapping(gate) for gate in raw_gates)

        if is_terminal:
            if guide is not None and not isinstance(guide, str):
                raise WorkflowError(f"Workflow validation failed: step {name} has an invalid guide")
        elif not isinstance(guide, str) or not guide.strip():
            raise WorkflowError(f"Workflow validation failed: step {name} has no non-empty inline guide")
        if sum(gate.type == "human" for gate in gates) > 1:
            raise WorkflowError(f"Workflow validation failed: step {name} has multiple human gates")
        if is_terminal and any(gate.type == "human" for gate in gates):
            raise WorkflowError(f"Workflow validation failed: terminal step {name} cannot contain a human gate")

        raw_producers = data.get("condition_producers", {})
        if not isinstance(raw_producers, Mapping):
            raise WorkflowError(f"Workflow validation failed: step {name} condition_producers must be a mapping")
        producers = tuple(
            Producer.from_mapping(str(variable), producer)
            for variable, producer in raw_producers.items()
        )

        raw_transitions = data.get("transitions", [])
        if not isinstance(raw_transitions, list):
            raise WorkflowError(f"Workflow validation failed: step {name} transitions must be a list")
        transitions = tuple(
            Transition.from_mapping(name, transition)
            if isinstance(transition, Mapping)
            else None
            for transition in raw_transitions
        )
        if any(transition is None for transition in transitions):
            raise WorkflowError(f"Workflow validation failed: step {name} has a non-mapping transition")
        return cls(
            name=name,
            guide=guide,
            gates=gates,
            producers=producers,
            transitions=tuple(transitions),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class Workflow:
    entry: str
    terminal: str
    steps: dict[str, Step]
    producer_timeout_seconds: int

    @classmethod
    def from_yaml(cls, path: Path) -> "Workflow":
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except OSError as error:
            raise WorkflowError("Workflow validation failed: workflow file could not be read") from error
        except yaml.YAMLError as error:
            raise WorkflowError("Workflow validation failed: workflow YAML is invalid") from error
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: object) -> "Workflow":
        if not isinstance(data, Mapping):
            raise WorkflowError("Workflow validation failed: workflow YAML is not a mapping")
        if data.get("version") != "v2" or "transitions" in data:
            raise WorkflowError("Workflow validation failed: workflow version must be v2")

        entry = data.get("entry")
        terminal = data.get("terminal")
        raw_steps = data.get("steps")
        if not isinstance(entry, str) or not entry:
            raise WorkflowError("Workflow validation failed: entry step is missing")
        if not isinstance(terminal, str) or not terminal:
            raise WorkflowError("Workflow validation failed: terminal step is missing")
        if not isinstance(raw_steps, Mapping):
            raise WorkflowError("Workflow validation failed: steps must be a mapping")
        if entry == terminal:
            raise WorkflowError("Workflow validation failed: entry and terminal steps must differ")

        timeout = data.get("producer_timeout_seconds", 30)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 300:
            raise WorkflowError("Workflow validation failed: producer_timeout_seconds must be 1 to 300")

        steps: dict[str, Step] = {}
        for name, step_data in raw_steps.items():
            if not isinstance(name, str) or not name or not isinstance(step_data, Mapping):
                raise WorkflowError("Workflow validation failed: each step must be a non-empty mapping")
            steps[name] = Step.from_mapping(name, step_data, name == terminal)
        if entry not in steps:
            raise WorkflowError("Workflow validation failed: entry step is missing")
        if terminal not in steps:
            raise WorkflowError("Workflow validation failed: terminal step is missing")

        producer_variables: set[str] = set()
        for step in steps.values():
            referenced_variables = {
                transition.condition.variable
                for transition in step.transitions
                if transition.condition is not None
            }
            if not referenced_variables and step.producers:
                raise WorkflowError(
                    f"Workflow validation failed: step {step.name} has an unused condition producer"
                )
            if not referenced_variables.issuperset({producer.variable for producer in step.producers}):
                raise WorkflowError(
                    f"Workflow validation failed: step {step.name} has a producer not used by its routes"
                )
            for producer in step.producers:
                if producer.variable in producer_variables:
                    raise WorkflowError(
                        f"Workflow validation failed: condition variable {producer.variable} has multiple producers"
                    )
                producer_variables.add(producer.variable)

            if step.name == terminal and step.transitions:
                raise WorkflowError(f"Workflow validation failed: terminal step {terminal} has an outgoing transition")
            targets = [transition.to_step for transition in step.transitions]
            if len(targets) != len(set(targets)):
                raise WorkflowError(f"Workflow validation failed: step {step.name} has duplicate candidate targets")
            if len([transition for transition in step.transitions if transition.default]) > 1:
                raise WorkflowError(f"Workflow validation failed: step {step.name} has multiple default transitions")
            conditions = [
                transition.condition.text()
                for transition in step.transitions
                if transition.condition is not None
            ]
            if len(conditions) != len(set(conditions)):
                raise WorkflowError(f"Workflow validation failed: step {step.name} has duplicate when predicates")
            for transition in step.transitions:
                if transition.to_step not in steps:
                    raise WorkflowError(f"Workflow validation failed: step {step.name} has an unknown target step")
                if transition.to_step == step.name:
                    raise WorkflowError(f"Workflow validation failed: step {step.name} has a self-loop")
            if step.name != terminal and not step.transitions:
                raise WorkflowError(f"Workflow validation failed: step {step.name} has no candidate transitions")

        reachable: set[str] = set()
        queue: deque[str] = deque([entry])
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(transition.to_step for transition in steps[current].transitions)
        unreachable = sorted(set(steps) - reachable)
        if unreachable:
            raise WorkflowError(
                f"Workflow validation failed: unreachable step {unreachable[0]}"
            )

        for name in steps:
            if not _has_terminal_path(name, steps, terminal):
                raise WorkflowError(
                    f"Workflow validation failed: step {name} has no static path to terminal"
                )

        return cls(
            entry=entry,
            terminal=terminal,
            steps=steps,
            producer_timeout_seconds=timeout,
        )

    def template_references(self) -> set[str]:
        references: set[str] = set()

        def collect(value: str, _field: str) -> str:
            references.update(extract_template_references(value))
            return value

        for step in self.steps.values():
            replace_step_templates(step, collect)
        return references

    def step(self, name: str) -> Step:
        return self.steps[name]


def _has_terminal_path(
    start: str,
    steps: dict[str, Step],
    terminal: str,
) -> bool:
    reachable: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current == terminal:
            return True
        if current in reachable:
            continue
        reachable.add(current)
        stack.extend(
            transition.to_step
            for transition in steps[current].transitions
            if transition.to_step not in reachable
        )
    return False
