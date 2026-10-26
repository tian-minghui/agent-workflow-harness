from __future__ import annotations

import os
import json
import subprocess
import sys

from pathlib import Path
from typing import Iterable, Mapping, Sequence


import yaml


def file_gate(gate_id: str, path: str) -> dict[str, object]:
    return {"id": gate_id, "type": "file_exists", "path": path}


def command_gate(gate_id: str, command: str) -> dict[str, object]:
    return {"id": gate_id, "type": "command", "command": command}


def transition(source: str, target: str) -> dict[str, str]:
    return {"from": source, "to": target}


def write_workflow(
    root: Path,
    *,
    entry: str,
    terminal: str,
    steps: Mapping[str, Mapping[str, object]],
    transitions: Sequence[Mapping[str, str]],
) -> Path:
    """Write a schema-v2 package while preserving the old helper call shape."""
    document_steps = dict(steps)
    for transition_edge in transitions:
        source = transition_edge["from"]
        step = dict(document_steps[source])
        candidate = {"to": transition_edge["to"]}
        if "when" in transition_edge:
            candidate["when"] = transition_edge["when"]
        else:
            candidate["default"] = True
        step["transitions"] = [*step.get("transitions", []), candidate]
        document_steps[source] = step
    data = {
        "version": "v2",
        "entry": entry,
        "terminal": terminal,
        "steps": document_steps,
    }
    workflow = root / "workflow.yaml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return workflow


def standard_workflow(
    root: Path,
    *,
    design_gates: Iterable[dict[str, object]] | None = None,
    implementation_gates: Iterable[dict[str, object]] | None = None,
    design_guide: str | None = "Read and think.",
    implementation_guide: str | None = "Implement the design.",
    terminal_guide: str | None = None,
) -> Path:
    steps = {
        "design": {"title": "Technical design", "guide": design_guide, "gates": list(design_gates or [])},
        "implementation": {
            "title": "Implementation",
            "guide": implementation_guide,
            "gates": list(implementation_gates or []),
        },
        "done": {"title": "Done", "guide": terminal_guide, "gates": []},
    }
    return write_workflow(
        root,
        entry="design",
        terminal="done",
        steps=steps,
        transitions=[
            transition("design", "implementation"),
            transition("implementation", "done"),
        ],
    )


def run_wf(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the workflow CLI through its public python -m entry point."""
    complete_env = env if env is not None else os.environ.copy()
    repo_root = Path(__file__).resolve().parents[1]
    existing_path = complete_env.get("PYTHONPATH", "")
    complete_env["PYTHONPATH"] = str(repo_root) + os.pathsep + existing_path
    return subprocess.run(
        [sys.executable, "-m", "agent_workflow_harness", *args],
        text=True,
        capture_output=True,
        check=False,
        cwd=cwd,
        env=complete_env,
    )


def human_gate(gate_id: str, request: str, evidence: Sequence[str]) -> dict[str, object]:
    return {
        "id": gate_id,
        "type": "human",
        "request": request,
        "evidence": list(evidence),
    }

def install_source_package(
    root: Path,
    alias: str,
    *,
    workflow: Path | None = None,
    content: str | None = None,
) -> Path:
    """Install a directory-backed source package under an isolated home/project root."""
    package = root / ".agents" / "workflows" / alias
    package.mkdir(parents=True, exist_ok=True)
    definition = package / "workflow.yaml"
    if workflow is not None:
        definition.write_text(workflow.read_text(encoding="utf-8"), encoding="utf-8")
    elif content is not None:
        definition.write_text(content, encoding="utf-8")
    else:
        raise ValueError("install_source_package requires workflow or content")
    return package


def active_state(project: Path) -> dict[str, object]:
    """Read the active task state from the public runtime file layout."""
    pointer_path = project / ".workflow-harness" / "task.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    state_path = (
        project / ".workflow-harness" / "tasks" / str(pointer["task_id"]) / "state.json"
    )
    return json.loads(state_path.read_text(encoding="utf-8"))


def active_artifact_dir(project: Path) -> Path:
    return project / str(active_state(project)["artifact_dir"])
