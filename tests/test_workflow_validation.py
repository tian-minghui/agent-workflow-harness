from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class WorkflowValidationTest(unittest.TestCase):
    """Black-box workflow validation through the agent-blind start command."""

    def _git_project(self, root: Path) -> tuple[Path, Path]:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        return project, root / "home"

    def _install_alias(self, home, *, workflow: Path | None = None, content: str | None = None) -> Path:
        return helpers.install_source_package(
            home,
            "frontend-delivery",
            workflow=workflow,
            content=content,
        )

    def _start(self, project: Path, home: Path):
        return helpers.run_wf(
            "start",
            "frontend-delivery",
            "--task",
            "Fix login timeout",
            cwd=project,
            env={**os.environ, "HOME": str(home)},
        )

    def run_validation(self, workflow: Path | None = None, content: str | None = None) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._git_project(root)
            self._install_alias(home, workflow=workflow, content=content)
            completed = self._start(project, home)
            return json.loads(completed.stdout or "{}")

    def test_invalid_yaml_is_rejected(self) -> None:
        payload = self.run_validation(content="entry: [")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["reason"], "Workflow definition is invalid or incomplete")

    def test_non_terminal_empty_guide_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = helpers.standard_workflow(Path(temp_dir), design_guide="")
            payload = self.run_validation(workflow=workflow)
            self.assertEqual(payload["reason"], "Workflow definition is invalid or incomplete")

    def test_non_terminal_self_loop_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = helpers.write_workflow(
                Path(temp_dir),
                entry="design",
                terminal="implement",
                steps={
                    "design": {"title": "Design", "guide": "Read and think.", "gates": []},
                    "implement": {"title": "Implement", "guide": None, "gates": []},
                },
                transitions=[helpers.transition("design", "design")],
            )
            payload = self.run_validation(workflow=workflow)
            self.assertEqual(payload["reason"], "Workflow definition is invalid or incomplete")

    def test_multiple_outgoing_transitions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = helpers.write_workflow(
                Path(temp_dir),
                entry="design",
                terminal="done",
                steps={
                    "design": {"title": "Design", "guide": "Read and think.", "gates": []},
                    "implement": {"title": "Implement", "guide": "Implement.", "gates": []},
                    "done": {"title": "Done", "guide": None, "gates": []},
                },
                transitions=[
                    helpers.transition("design", "implement"),
                    helpers.transition("design", "done"),
                ],
            )
            payload = self.run_validation(workflow=workflow)
            self.assertEqual(payload["reason"], "Workflow definition is invalid or incomplete")

    def test_optional_gates_and_null_terminal_guide_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = helpers.write_workflow(
                Path(temp_dir),
                entry="design",
                terminal="implement",
                steps={
                    "design": {"title": "Design", "guide": "Read and think."},
                    "implement": {"title": "Implement", "guide": None},
                },
                transitions=[helpers.transition("design", "implement")],
            )
            payload = self.run_validation(workflow=workflow)
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["instruction"], "Read and think.")

    def test_missing_gates_key_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = helpers.write_workflow(
                Path(temp_dir),
                entry="design",
                terminal="implement",
                steps={
                    "design": {"title": "Design", "guide": "Read and think."},
                    "implement": {"title": "Implement", "guide": None},
                },
                transitions=[helpers.transition("design", "implement")],
            )
            payload = self.run_validation(workflow=workflow)
            self.assertEqual(payload["status"], "active")


if __name__ == "__main__":
    unittest.main()
