from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from agent_workflow_harness.workflow import Gate, Step


ANSI_ESCAPE_PATTERN = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\][0-9;?]*(?:\x07|\x1b\\)|[@-Z\\])")
MAX_COMMAND_OUTPUT_CHARS = 1500


@dataclass(frozen=True)
class GateOutcome:
    gate_id: str
    reason: str

def _bounded_output(stdout: str, stderr: str) -> str:
    combined_output = stdout
    if stderr:
        if combined_output:
            combined_output += "\n"
        combined_output += stderr
    cleaned_output = ANSI_ESCAPE_PATTERN.sub("", combined_output).rstrip()
    if len(cleaned_output) > MAX_COMMAND_OUTPUT_CHARS:
        cleaned_output = "..." + cleaned_output[-MAX_COMMAND_OUTPUT_CHARS:]
    return cleaned_output


def evaluate(
    step: Step,
    project_directory: Path,
    workflow_directory: Path,
) -> GateOutcome | None:
    automatic_gates = tuple(gate for gate in step.gates if gate.type != "human")
    return _run_gates(automatic_gates, project_directory, workflow_directory)


def _run_gates(
    gates: tuple[Gate, ...],
    project_directory: Path,
    workflow_directory: Path,
) -> GateOutcome | None:
    for gate in gates:
        if gate.type == "file_exists":
            path = project_directory / str(gate.path)
            if not path.exists():
                return GateOutcome(gate.id, f"{gate.path} does not exist")
        elif gate.type == "workflow_script":
            if gate.script is None:
                continue
            script_path = workflow_directory / gate.script
            if not script_path.is_file():
                return GateOutcome(gate.id, f"workflow resource {gate.script} does not exist")
            # Flags must reach workflow scripts verbatim; only their path operands
            # are resolved relative to the project directory.
            project_args = [
                value if value.startswith("-") else str(project_directory / value)
                for value in gate.project_args
            ]
            result = subprocess.run(
                [sys.executable, str(script_path), *project_args],
                cwd=project_directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0:
                cleaned_process_output = _bounded_output(result.stdout, result.stderr)
                if not cleaned_process_output:
                    return GateOutcome(gate.id, "Workflow script failed with no output")
                return GateOutcome(gate.id, cleaned_process_output)
        elif gate.type == "command":
            command = gate.command or ""
            result = subprocess.run(
                command,
                cwd=project_directory,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0:
                cleaned_output = _bounded_output(result.stdout, result.stderr)
                if not cleaned_output:
                    return GateOutcome(gate.id, "Command failed with no output")
                return GateOutcome(gate.id, cleaned_output)
    return None
