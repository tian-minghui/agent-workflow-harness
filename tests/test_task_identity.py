from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class TaskIdentityConflictTest(unittest.TestCase):
    """Exact task matching, conflict handling, and pointer-integrity behavior."""

    def _make_project(self, root: Path) -> tuple[Path, Path]:
        project = root / "demo-project"
        project.mkdir()
        home = root / "home"
        workflow = helpers.standard_workflow(
            home,
            design_gates=[helpers.file_gate("requirements", "docs/requirements.md")],
        )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)
        return project, home

    def _env(self, home: Path) -> dict[str, str]:
        return {**os.environ, "HOME": str(home)}

    def _start(self, project: Path, home: Path, title: str):
        return helpers.run_wf(
            "start",
            "frontend-delivery",
            "--task",
            title,
            cwd=project,
            env=self._env(home),
        )

    def _next(self, project: Path, home: Path):
        return helpers.run_wf("next", cwd=project, env=self._env(home))

    def test_repeated_start_with_same_title_resumes_then_existing_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._make_project(root)

            first = self._start(project, home, "Fix login timeout")
            second = self._start(project, home, "Fix login timeout")

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
            tasks = project / ".workflow-harness" / "tasks"
            self.assertEqual(len(list(tasks.iterdir())), 1)

    def test_starting_a_different_task_conflicts_without_switch_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._make_project(root)

            first = self._start(project, home, "Fix login timeout")
            second = self._start(project, home, "Fix export blank screen")

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 1)

            payload = json.loads(second.stdout)
            self.assertEqual(payload["status"], "conflict")
            self.assertEqual(payload["active_task"], {"title": "Fix login timeout"})
            self.assertIn("Project already has an active workflow task", payload["reason"])
            self.assertIn("Use awh next to continue the active task", payload["hint"])
            self.assertEqual(len(list((project / ".workflow-harness" / "tasks").iterdir())), 1)

    def test_deleted_pointer_is_not_recreated_by_next(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._make_project(root)
            self._start(project, home, "Fix login timeout")

            anchor = project / ".workflow-harness" / "task.json"
            anchor.unlink()

            completed = self._next(project, home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["reason"], "No active workflow task")
            self.assertFalse(anchor.exists())

    def test_a_pointer_without_a_task_identity_cannot_start_a_new_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._make_project(root)
            runtime = project / ".workflow-harness"
            runtime.mkdir()
            (runtime / "task.json").write_text(
                json.dumps(
                    {
                        "schema": "agent-workflow-harness.task-anchor.v1",
                        "workflow_alias": "frontend-delivery",
                        "title": "Fix login timeout",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = self._start(project, home, "Fix login timeout")
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("task pointer is invalid", payload["reason"])
            self.assertFalse((runtime / "tasks").exists())


if __name__ == "__main__":
    unittest.main()
