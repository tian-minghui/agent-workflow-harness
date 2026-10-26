from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class WorkflowStartTest(unittest.TestCase):
    """Black-box tests for the `awh start` public seam."""

    def _start(self, alias: str, title: str, *, project: Path, home: Path):
        return helpers.run_wf(
            "start",
            alias,
            "--task",
            title,
            cwd=project,
            env={**os.environ, "HOME": str(home)},
        )

    def test_start_with_builtin_alias_creates_a_project_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "demo-project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            completed = self._start(
                "frontend-delivery",
                "Fix login timeout",
                project=project,
                home=home,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(set(payload), {"status", "task", "instruction"})
            self.assertEqual(payload["status"], "active")
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
            self.assertIn(
                f"把结论整理到 {state['artifact_dir']}/requirements.md。",
                payload["instruction"],
            )

            runtime = project / ".workflow-harness"
            anchor = json.loads((runtime / "task.json").read_text(encoding="utf-8"))
            self.assertEqual(
                anchor,
                {
                    "schema": "agent-workflow-harness.task-anchor.v1",
                    "task_id": anchor["task_id"],
                    "workflow_alias": "frontend-delivery",
                    "title": "Fix login timeout",
                },
            )
            self.assertTrue((runtime / "tasks").is_dir())

    def test_user_alias_overrides_builtin_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "demo-project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            custom = helpers.standard_workflow(
                home,
                design_guide="Custom first-stage instruction.",
            )
            helpers.install_source_package(home, "frontend-delivery", workflow=custom)

            completed = self._start(
                "frontend-delivery",
                "Fix login timeout",
                project=project,
                home=home,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                json.loads(completed.stdout)["instruction"],
                "Custom first-stage instruction.",
            )

    def test_unknown_alias_returns_error_without_creating_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "demo-project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            completed = self._start(
                "missing-alias",
                "Fix login timeout",
                project=project,
                home=home,
            )
            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("missing-alias", payload["reason"])
            self.assertIn("Run awh start <workflow-alias> --task <title>", payload["hint"])
            self.assertFalse((project / ".workflow-harness").exists())

    def test_start_requires_a_natural_english_single_line_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "demo-project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            completed = self._start(
                "frontend-delivery",
                "修复\n登录超时",
                project=project,
                home=home,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Task title must be a natural English line", payload["reason"])
            self.assertFalse((project / ".workflow-harness").exists())


if __name__ == "__main__":
    unittest.main()
