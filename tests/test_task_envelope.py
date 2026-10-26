from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class TaskEnvelopeTest(unittest.TestCase):
    """Black-box tests for the enriched task envelope returned by task commands."""

    def _setup(self, root: Path):
        project = root / "project"
        home = root / "home"
        project.mkdir()
        home.mkdir()
        workflow = helpers.standard_workflow(
            home,
            design_gates=[helpers.human_gate("review", "请确认需求。", ["docs/requirements.md"])],
            implementation_guide="Implement the design.",
        )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)
        env = {**os.environ, "HOME": str(home)}
        return project, env

    def _run(self, *args: str, project: Path, env: dict[str, str]):
        return helpers.run_wf(*args, cwd=project, env=env)

    def _assert_task(self, payload: dict[str, object], project: Path) -> None:
        state = helpers.active_state(project)
        self.assertEqual(
            payload["task"],
            {
                "id": state["task_id"],
                "title": state["title"],
                "step": state["step"],
                "artifactDir": state["artifact_dir"],
            },
        )

    def test_every_task_command_returns_authoritative_task_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, env = self._setup(root)

            started = self._run(
                "start", "frontend-delivery", "--task", "Fix login timeout",
                project=project, env=env,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            self._assert_task(json.loads(started.stdout), project)

            evidence = project / "docs" / "requirements.md"
            evidence.parent.mkdir(parents=True)
            evidence.write_text("目标\n", encoding="utf-8")

            pending = self._run("next", project=project, env=env)
            self.assertEqual(pending.returncode, 1, pending.stderr)
            self._assert_task(json.loads(pending.stdout), project)

            rejected = self._run("reject", "--reason", "请补充兼容性", project=project, env=env)
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self._assert_task(json.loads(rejected.stdout), project)

            evidence.write_text("目标：Fix login timeout。\n", encoding="utf-8")
            refreshed = self._run("next", project=project, env=env)
            self._assert_task(json.loads(refreshed.stdout), project)

            approved = self._run("approve", "--note", "确认需求", project=project, env=env)
            self.assertEqual(approved.returncode, 1, approved.stderr)
            self._assert_task(json.loads(approved.stdout), project)

            advanced = self._run("next", project=project, env=env)
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self._assert_task(json.loads(advanced.stdout), project)


if __name__ == "__main__":
    unittest.main()
