import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class ControlPlaneNextTest(unittest.TestCase):
    """Black-box tests for the agent-blind control-plane `awh next` seam."""

    def _template_project(self, root: Path) -> Path:
        project = root / "demo-project"
        project.mkdir()
        home = root / "home"
        workflow = helpers.standard_workflow(
            home,
            design_gates=[helpers.file_gate("requirements", "docs/requirements.md")],
        )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)
        return project

    def _start(self, title: str, *, project: Path, home: Path):
        return helpers.run_wf(
            "start",
            "frontend-delivery",
            "--task",
            title,
            cwd=project,
            env={**os.environ, "HOME": str(home)},
        )

    def _next(self, *, project: Path, home: Path):
        return helpers.run_wf(
            "next",
            cwd=project,
            env={**os.environ, "HOME": str(home)},
        )

    def test_file_gate_blocks_next_on_the_active_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._template_project(root)
            home = root / "home"

            start = self._start("Fix login timeout", project=project, home=home)
            self.assertEqual(start.returncode, 0, start.stderr)

            completed = self._next(project=project, home=home)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "blocked")
            state = helpers.active_state(project)
            self.assertEqual(
                payload["task"],
                {
                    "id": state["task_id"],
                    "title": "Fix login timeout",
                    "step": state["step"],
                    "artifactDir": state["artifact_dir"],
                },
            )
            self.assertEqual(payload["instruction"], "Read and think.")
            self.assertEqual(
                payload["check"],
                {"gate": "requirements", "reason": "docs/requirements.md does not exist"},
            )

    def test_passing_gate_advances_to_the_next_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._template_project(root)
            home = root / "home"
            self._start("Fix login timeout", project=project, home=home)
            (project / "docs" / "requirements.md").parent.mkdir(parents=True)
            (project / "docs" / "requirements.md").write_text("Goal\n", encoding="utf-8")

            completed = self._next(project=project, home=home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["instruction"], "Implement the design.")

    def test_terminal_transition_stops_the_active_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._template_project(root)
            home = root / "home"
            self._start("Fix login timeout", project=project, home=home)
            (project / "docs" / "requirements.md").parent.mkdir(parents=True)
            (project / "docs" / "requirements.md").write_text("Goal\n", encoding="utf-8")
            self._next(project=project, home=home)

            completed = self._next(project=project, home=home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "done")
            self.assertFalse((project / ".workflow-harness" / "task.json").exists())


if __name__ == "__main__":
    unittest.main()
