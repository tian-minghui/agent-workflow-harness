from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class SourceBackedPackageResolutionTest(unittest.TestCase):
    """Source-backed workflow packages resolve from project, user, then built-in roots."""

    def _project(self, root: Path) -> Path:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        return project

    def _write_source_package(self, root: Path, alias: str, guide: str) -> Path:
        package_dir = root / ".agents" / "workflows" / alias
        package_dir.mkdir(parents=True, exist_ok=True)
        helpers.standard_workflow(package_dir, design_guide=guide)
        return package_dir

    def _start(
        self,
        project: Path,
        *,
        home: Path,
        alias: str = "source-demo",
        title: str = "Validate source-backed workflow",
    ):
        return helpers.run_wf(
            "start",
            alias,
            "--task",
            title,
            cwd=project,
            env={
                **__import__("os").environ,
                "HOME": str(home),
            },
        )

    def _active_task_dir(self, project: Path) -> Path:
        pointer = json.loads(
            (project / ".workflow-harness" / "task.json").read_text(encoding="utf-8")
        )
        return project / ".workflow-harness" / "tasks" / pointer["task_id"]

    def test_project_package_overrides_user_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()

            project_package = self._write_source_package(project, "source-demo", "Project workflow")
            self._write_source_package(home, "source-demo", "User workflow")

            start = self._start(project, home=home)
            self.assertEqual(start.returncode, 0, start.stderr)
            payload = json.loads(start.stdout)
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["instruction"], "Project workflow")
            state = json.loads((self._active_task_dir(project) / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(state["workflow_dir"]).resolve(), project_package.resolve())

    def test_user_package_is_used_when_project_package_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            user_package = self._write_source_package(home, "source-demo", "User workflow")

            start = self._start(project, home=home)
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertEqual(json.loads(start.stdout)["instruction"], "User workflow")
            state = json.loads((self._active_task_dir(project) / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(state["workflow_dir"]).resolve(), user_package.resolve())

    def test_start_records_source_package_and_definition_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            package_dir = self._write_source_package(project, "source-demo", "Project workflow")

            start = self._start(project, home=home)
            self.assertEqual(start.returncode, 0, start.stderr)

            state_path = self._active_task_dir(project) / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(Path(state["workflow_dir"]).resolve(), package_dir.resolve())
            self.assertRegex(str(state["workflow_yaml_sha256"]), r"^[a-f0-9]{64}$")
            self.assertEqual(state["workflow_alias"], "source-demo")
            self.assertEqual(state["title"], "Validate source-backed workflow")
            self.assertEqual(state["schema"], "agent-workflow-harness.task-state.v2")
            self.assertFalse((self._active_task_dir(project) / "workflow.snapshot.yaml").exists())
            self.assertFalse((self._active_task_dir(project) / "workflow.package").exists())

    def test_user_package_overrides_builtin_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            self._write_source_package(home, "frontend-delivery", "User overrides builtin")

            start = self._start(
                project,
                home=home,
                alias="frontend-delivery",
                title="Validate user workflow override",
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertEqual(json.loads(start.stdout)["instruction"], "User overrides builtin")

    def test_source_backed_run_reads_the_package_directory_directly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            package_dir = self._write_source_package(project, "source-demo", "Project workflow")

            start = self._start(project, home=home)
            self.assertEqual(start.returncode, 0, start.stderr)
            task_dir = self._active_task_dir(project)
            self.assertFalse((task_dir / "workflow.package").exists())
            self.assertFalse((task_dir / "workflow.snapshot.yaml").exists())

            docs = project / "docs" / "requirements.md"
            docs.parent.mkdir(parents=True)
            docs.write_text("Source package direct\n", encoding="utf-8")
            second = helpers.run_wf(
                "next",
                cwd=project,
                env={**__import__("os").environ, "HOME": str(home)},
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["status"], "active")
            self.assertTrue((package_dir / "workflow.yaml").is_file())

    def test_project_source_package_runs_from_a_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            package_dir = self._write_source_package(project, "source-demo", "Project workflow")
            subdirectory = project / "src"
            subdirectory.mkdir()

            start = helpers.run_wf(
                "start",
                "source-demo",
                "--task",
                "Validate source package path",
                cwd=subdirectory,
                env={**__import__("os").environ, "HOME": str(home)},
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertEqual(json.loads(start.stdout)["instruction"], "Project workflow")
            state = json.loads((self._active_task_dir(project) / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(state["workflow_dir"]).resolve(), package_dir.resolve())

    def test_source_demo_alias_without_any_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()

            start = self._start(project, home=home)
            self.assertEqual(start.returncode, 1)
            payload = json.loads(start.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Workflow alias not found: source-demo", payload["reason"])

    def test_builtin_workflow_is_source_backed_package(self) -> None:
        package_root = Path("agent_workflow_harness") / "workflows"
        self.assertTrue((package_root / "frontend-delivery" / "workflow.yaml").is_file())
        self.assertTrue((package_root / "meeting-summary" / "workflow.yaml").is_file())
        self.assertFalse((package_root / "meeting-summary.yaml").exists())


if __name__ == "__main__":
    unittest.main()
