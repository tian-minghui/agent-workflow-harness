from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class WorkflowBundleTest(unittest.TestCase):
    """Directory source packages and resource-backed gates."""

    def _project(self, root: Path) -> Path:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        return project

    def _install_bundle(self, home: Path, alias: str = "bundle-demo") -> tuple[Path, Path]:
        package_root = home / ".agents" / "workflows" / alias
        resources = package_root / "resources"
        resources.mkdir(parents=True)

        workflow_data = {
            "version": "v2",
            "entry": "prepare",
            "terminal": "done",
            "steps": {
                "prepare": {
                    "title": "Prepare",
                    "guide": "Create the required artifact.",
                    "gates": [
                        {
                            "id": "artifact",
                            "type": "workflow_script",
                            "script": "resources/check_artifact.py",
                            "project_args": ["docs/requirements.md"],
                        }
                    ],
                    "transitions": [{"to": "done", "default": True}],
                },
                "done": {"title": "Done", "guide": None, "gates": []},
            },
        }
        import yaml

        (package_root / "workflow.yaml").write_text(
            yaml.safe_dump(workflow_data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return package_root, resources

    def _run(self, *args: str, project: Path, home: Path):
        return helpers.run_wf(
            *args,
            cwd=project,
            env={**os.environ, "HOME": str(home)},
        )

    def test_resource_gate_reads_from_the_source_package_without_a_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            package, resources = self._install_bundle(home)
            (resources / "check_artifact.py").write_text(
                """from pathlib import Path
import sys
path = Path(sys.argv[1])
if "bundle target" not in path.read_text():
    raise SystemExit("docs/requirements.md 缺少 bundle target")
""",
                encoding="utf-8",
            )

            start = self._run(
                "start", "bundle-demo", "--task", "Implement workflow bundle", project=project, home=home
            )
            self.assertEqual(start.returncode, 0, start.stderr)

            pointer_path = project / ".workflow-harness" / "task.json"
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            task_dir = pointer_path.parent / "tasks" / str(pointer["task_id"])
            self.assertFalse((task_dir / "workflow.snapshot.yaml").exists())
            self.assertFalse((task_dir / "workflow.package").exists())
            state = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(str(state["workflow_dir"])).resolve(), package.resolve())

            docs = project / "docs" / "requirements.md"
            docs.parent.mkdir(parents=True)
            docs.write_text("bundle target\n", encoding="utf-8")
            advanced = self._run("next", project=project, home=home)
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            done_state = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
            payload = json.loads(advanced.stdout)
            self.assertEqual(payload["status"], "done")
            self.assertEqual(
                payload["task"],
                {
                    "id": pointer["task_id"],
                    "title": pointer["title"],
                    "step": done_state["step"],
                    "artifactDir": done_state["artifact_dir"],
                },
            )

    def test_resource_gate_failure_is_bounded_and_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            _, resources = self._install_bundle(home)
            (resources / "check_artifact.py").write_text(
                """import sys
from pathlib import Path
path = Path(sys.argv[1])
if path.read_text() != "workflow resource ready\\n":
    raise SystemExit("docs/requirements.md 内容不是 workflow resource ready")
""",
                encoding="utf-8",
            )

            start = self._run(
                "start", "bundle-demo", "--task", "Test resource gate failure", project=project, home=home
            )
            self.assertEqual(start.returncode, 0, start.stderr)

            docs = project / "docs" / "requirements.md"
            docs.parent.mkdir(parents=True)
            docs.write_text("wrong content\n", encoding="utf-8")
            completed = self._run("next", project=project, home=home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["check"]["gate"], "artifact")
            self.assertEqual(
                payload["check"]["reason"],
                "docs/requirements.md 内容不是 workflow resource ready",
            )

    def test_standalone_yaml_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            standalone = home / "workflows" / "legacy-demo.yaml"
            standalone.parent.mkdir(parents=True)
            standalone.write_text("version: v1\n", encoding="utf-8")

            start = self._run(
                "start", "legacy-demo", "--task", "Reject legacy YAML alias", project=project, home=home
            )
            self.assertEqual(start.returncode, 1)
            self.assertEqual(json.loads(start.stdout)["status"], "error")
            self.assertFalse((project / ".workflow-harness").exists())


if __name__ == "__main__":
    unittest.main()
