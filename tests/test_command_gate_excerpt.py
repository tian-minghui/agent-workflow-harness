from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class CommandGateExcerptTest(unittest.TestCase):
    """Black-box tests for command-gate failure reasons and project-rooted execution."""

    def _make_git_project(self, root: Path) -> tuple[Path, Path, Path]:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(
            ["git", "init", "--quiet", str(project)],
            check=True,
        )
        subdirectory = project / "src"
        subdirectory.mkdir()
        return project, subdirectory, root

    def _install_alias(self, home: Path, command: str) -> None:
        workflow = helpers.standard_workflow(
            home,
            design_gates=[helpers.command_gate("check", command)],
        )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)

    def _start(
        self,
        project: Path,
        wf_home: Path,
    ):
        return helpers.run_wf(
            "start",
            "frontend-delivery",
            "--task",
            "Fix login timeout",
            cwd=project,
            env={**os.environ, "HOME": str(wf_home)},
        )

    def test_command_gate_blocks_with_a_tail_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, subdirectory, _ = self._make_git_project(root)
            wf_home = root / "workflow-home"
            self._install_alias(
                wf_home,
                "python3 -c \"print('测试输出' * 800); exit(1)\"",
            )

            start = self._start(project, wf_home)
            self.assertEqual(start.returncode, 0, start.stderr)
            (project / "docs").mkdir()
            (project / "docs" / "requirements.md").write_text("Goal", encoding="utf-8")

            completed = helpers.run_wf(
                "next",
                cwd=subdirectory,
                env={**os.environ, "HOME": str(wf_home)},
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("测试输出", payload["check"]["reason"])
            self.assertTrue(payload["check"]["reason"].startswith("..."))
            self.assertLessEqual(len(payload["check"]["reason"]), 1503)

    def test_command_gate_without_output_returns_a_fixed_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, _ = self._make_git_project(root)
            wf_home = root / "workflow-home"
            self._install_alias(wf_home, "false")

            start = self._start(project, wf_home)
            self.assertEqual(start.returncode, 0, start.stderr)

            completed = helpers.run_wf(
                "next",
                cwd=project,
                env={**os.environ, "HOME": str(wf_home)},
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(
                payload["check"]["reason"],
                "Command failed with no output",
            )

    def test_command_gate_runs_against_the_project_root_from_a_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, subdirectory, _ = self._make_git_project(root)
            wf_home = root / "workflow-home"
            self._install_alias(wf_home, "pwd; exit 1")

            start = self._start(project, wf_home)
            self.assertEqual(start.returncode, 0, start.stderr)

            completed = helpers.run_wf(
                "next",
                cwd=subdirectory,
                env={**os.environ, "HOME": str(wf_home)},
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertIn(str(project), payload["check"]["reason"])


if __name__ == "__main__":
    unittest.main()
