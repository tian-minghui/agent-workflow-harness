from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class ApproveNextTest(unittest.TestCase):
    """Black-box tests for the opt-in record-and-continue approval command."""

    def _setup(self, root: Path):
        project = root / "project"
        home = root / "home"
        project.mkdir()
        home.mkdir()
        design_gates = [
            helpers.file_gate("requirements", "docs/requirements.md"),
            helpers.human_gate(
                "requirements_confirmed_by_user",
                "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                ["docs/requirements.md"],
            ),
        ]
        workflow = helpers.standard_workflow(
            home,
            design_gates=design_gates,
            design_guide="Read and think.",
            implementation_guide="Implement the design.",
        )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)
        started = helpers.run_wf(
            "start",
            "frontend-delivery",
            "--task",
            "Fix login timeout",
            cwd=project,
            env={**os.environ, "HOME": str(home)},
        )
        if started.returncode != 0:
            raise RuntimeError(started.stderr or started.stdout)
        return project, home, {**os.environ, "HOME": str(home)}

    def _write_evidence(self, project: Path, text: str = "Fix login timeout.\n") -> None:
        path = project / "docs" / "requirements.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _next(self, project: Path, env: dict[str, str]):
        return helpers.run_wf("next", cwd=project, env=env)

    def test_default_approval_is_record_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project)

            pending = self._next(project, env)
            self.assertEqual(pending.returncode, 1, pending.stderr)

            approved = helpers.run_wf("approve", cwd=project, env=env)
            self.assertEqual(approved.returncode, 1, approved.stderr)
            payload = json.loads(approved.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertTrue(payload["check"]["reason"].startswith("HUMAN_REVIEW_RECORDED:"))
            self.assertEqual(helpers.active_state(project)["step"], "design")

    def test_approve_next_advances_after_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project)
            self._next(project, env)

            completed = helpers.run_wf("approve", "--next", cwd=project, env=env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["instruction"], "Implement the design.")
            self.assertEqual(helpers.active_state(project)["step"], "implementation")

    def test_rejection_does_not_advance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project, "Initial target.\n")
            self._next(project, env)

            rejected = helpers.run_wf(
                "reject", "--reason", "请补充兼容性要求", cwd=project, env=env
            )
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            payload = json.loads(rejected.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(helpers.active_state(project)["step"], "design")

            self._write_evidence(project, "Fix login timeout; compatibility: Chrome.\n")
            changed = self._next(project, env)
            self.assertEqual(changed.returncode, 1, changed.stderr)

            completed = helpers.run_wf("approve", "--next", cwd=project, env=env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(helpers.active_state(project)["step"], "implementation")


if __name__ == "__main__":
    unittest.main()
