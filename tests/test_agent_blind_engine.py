from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class AgentBlindEngineTest(unittest.TestCase):
    """Black-box tests for the project-local runtime and clean v1.2 interface."""

    def _git_project(self, root: Path) -> Path:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        return project

    def _install_alias(self, home: Path, workflow: Path) -> Path:
        return helpers.install_source_package(home, "frontend-delivery", workflow=workflow)

    def _env(self, home: Path) -> dict[str, str]:
        return {**os.environ, "HOME": str(home)}

    def _start(
        self,
        project: Path,
        home: Path,
        alias: str = "frontend-delivery",
        title: str = "Fix login timeout",
    ):
        return helpers.run_wf(
            "start",
            alias,
            "--task",
            title,
            cwd=project,
            env=self._env(home),
        )

    def _next(self, project: Path, home: Path):
        return helpers.run_wf("next", cwd=project, env=self._env(home))

    def _active_task(self, project: Path) -> tuple[Path, Path]:
        runtime = project / ".workflow-harness"
        pointer = json.loads((runtime / "task.json").read_text(encoding="utf-8"))
        return runtime / "tasks" / str(pointer["task_id"]), runtime / "task.json"

    def test_workflow_definition_drift_stops_the_active_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()
            package_path = self._install_alias(
                home,
                helpers.standard_workflow(
                    home,
                    design_gates=[helpers.file_gate("requirements", "docs/requirements.md")],
                ),
            )
            definition_path = package_path / "workflow.yaml"

            first = self._start(project, home)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(first.stdout)["instruction"], "Read and think.")
            definition_path.write_text("expired workflow\n", encoding="utf-8")

            repeated = self._start(project, home)
            payload = json.loads(repeated.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Workflow definition source changed", payload["reason"])

            completed = self._next(project, home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Workflow definition source changed", payload["reason"])

    def test_corrupt_current_task_cannot_be_replaced_by_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()
            self._install_alias(
                home,
                helpers.standard_workflow(
                    home,
                    design_gates=[helpers.file_gate("requirements", "docs/requirements.md")],
                ),
            )

            first = self._start(project, home)
            self.assertEqual(first.returncode, 0, first.stderr)
            _, pointer_path = self._active_task(project)
            pointer_path.write_text("{ broken json", encoding="utf-8")

            replacement = self._start(project, home, title="Fix export blank screen")
            self.assertEqual(replacement.returncode, 1)
            payload = json.loads(replacement.stdout)
            self.assertEqual(payload, {"status": "error", "reason": "Active workflow task pointer is invalid or unreadable"})

    def test_repeated_start_with_corrupt_task_state_returns_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()
            self._install_alias(home, helpers.standard_workflow(home))
            self._start(project, home)
            task_dir, _ = self._active_task(project)
            (task_dir / "state.json").write_text("{ broken", encoding="utf-8")

            repeated = self._start(project, home)
            payload = json.loads(repeated.stdout)
            self.assertEqual(
                payload,
                {"status": "error", "reason": "Active workflow task state is invalid or unreadable"},
            )

    def test_missing_state_projection_is_an_operational_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()
            self._install_alias(
                home,
                helpers.standard_workflow(
                    home,
                    design_gates=[helpers.file_gate("requirements", "docs/requirements.md")],
                ),
            )
            self._start(project, home)
            task_dir, _ = self._active_task(project)
            state_path = task_dir / "state.json"
            state_path.unlink()

            completed = self._next(project, home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("active workflow task directory is missing", payload["reason"].lower())
            events = [
                json.loads(line)
                for line in (task_dir / "history.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(events[-1]["event"], "error")
            self.assertIn("state is missing", events[-1]["reason"])
            self.assertFalse(state_path.exists())

    def test_next_without_an_active_task_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()

            completed = self._next(project, home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["reason"], "No active workflow task")
            self.assertIn("Run awh start", payload["hint"])

    def test_explicit_project_override_resolves_the_requested_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            outside = root / "outside"
            outside.mkdir()
            home = root / "home"
            home.mkdir()

            completed = helpers.run_wf(
                "start",
                "frontend-delivery",
                "--task",
                "Fix login timeout",
                cwd=outside,
                env={**self._env(home), "AWH_PROJECT_DIR": str(project)},
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((project / ".workflow-harness" / "task.json").is_file())
            self.assertFalse((outside / ".workflow-harness" / "task.json").exists())

    def test_cli_rejects_direct_project_directory_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()

            completed = helpers.run_wf(
                "start",
                "frontend-delivery",
                "--task",
                "Fix login timeout",
                "--project-dir",
                str(project),
                cwd=project,
                env=self._env(home),
            )

            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertEqual(
                payload,
                {"status": "error", "reason": "Invalid command arguments", "hint": "Run awh --help"},
            )

    def test_alias_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()

            completed = self._start(project, home, alias="./../workflow")
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn(
                "Workflow aliases must use letters, digits, dots, underscores, or hyphens",
                payload["reason"],
            )
            self.assertFalse((project / ".workflow-harness").exists())

    def test_corrupt_current_task_returns_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()
            self._install_alias(home, helpers.standard_workflow(home))
            self._start(project, home)
            _, pointer_path = self._active_task(project)
            pointer_path.write_text("{ broken json", encoding="utf-8")

            completed = self._next(project, home)
            payload = json.loads(completed.stdout)
            self.assertEqual(
                payload,
                {"status": "error", "reason": "Active workflow task pointer is invalid or unreadable"},
            )

    def test_running_without_a_command_returns_stable_error_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()

            completed = helpers.run_wf(cwd=project, env=self._env(home))
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(
                json.loads(completed.stdout),
                {
                    "status": "error",
                    "reason": "A workflow command is required",
                    "hint": "Run awh start <workflow-alias> --task <title> or awh next",
                },
            )

    def test_legacy_workflow_and_task_directory_arguments_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._git_project(root)
            home = root / "home"
            home.mkdir()

            workflow_flag = helpers.run_wf(
                "next",
                "--workflow",
                str(root / "workflow.yaml"),
                cwd=project,
                env=self._env(home),
            )
            task_dir_flag = helpers.run_wf(
                "next",
                "--task-dir",
                str(root / "task"),
                cwd=project,
                env=self._env(home),
            )

            for result in (workflow_flag, task_dir_flag):
                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    json.loads(result.stdout),
                    {"status": "error", "reason": "Invalid command arguments", "hint": "Run awh --help"},
                )

    def test_builtin_examples_are_available_by_alias(self) -> None:
        aliases = [
            "frontend-delivery",
            "meeting-summary",
        ]
        for alias in aliases:
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as run_dir:
                root = Path(run_dir)
                project = self._git_project(root)
                home = root / "home"
                home.mkdir()
                completed = self._start(
                    project,
                    home,
                    alias=alias,
                    title=f"Run {alias} workflow task",
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "active")
                self.assertTrue(payload["instruction"].strip())


if __name__ == "__main__":
    unittest.main()
