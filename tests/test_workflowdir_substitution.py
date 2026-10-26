from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class WorkflowDirSubstitutionTest(unittest.TestCase):
    """One source-package token works in guide, command, human, and script seams."""

    def _project(self, root: Path) -> Path:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        return project

    def _package(self, root: Path, *, command: str, human_request: str | None, script_gate: bool = False) -> Path:
        package = root / ".agents" / "workflows" / "workflowdir-demo"
        package.mkdir(parents=True, exist_ok=True)
        gates: list[dict[str, object]] = [{"id": "source_file", "type": "command", "command": command}]
        if human_request is not None:
            gates.append({"id": "review", "type": "human", "request": human_request, "evidence": ["docs/requirements.md"]})
        if script_gate:
            gates.insert(
                0,
                {
                    "id": "script",
                    "type": "workflow_script",
                    "script": "scripts/check.py",
                    "project_args": ["docs/requirements.md"],
                },
            )
        helpers.write_workflow(
            package,
            entry="design",
            terminal="done",
            steps={
                "design": {
                    "title": "Design",
                    "guide": "Read ${workflowDir}/references/brief.md before continuing.",
                    "gates": gates,
                },
                "done": {"title": "Done", "guide": None, "gates": []},
            },
            transitions=[helpers.transition("design", "done")],
        )
        return package

    def _env(self, home: Path) -> dict[str, str]:
        return {**os.environ, "HOME": str(home)}

    def _run(self, *args: str, project: Path, home: Path):
        return helpers.run_wf(*args, cwd=project, env=self._env(home))

    def test_workflowdir_replaces_guide_and_human_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            package = self._package(project, command=":", human_request="Review ${workflowDir}/references/brief.md")
            (package / "references").mkdir()
            (package / "references" / "brief.md").write_text("brief\n", encoding="utf-8")

            start = self._run("start", "workflowdir-demo", "--task", "Validate path substitution", project=project, home=home)
            self.assertEqual(start.returncode, 0, start.stderr)
            payload = json.loads(start.stdout)
            self.assertEqual(set(payload), {"status", "task", "instruction"})
            self.assertEqual(
                payload["instruction"],
                f"Read {package.resolve()}/references/brief.md before continuing.",
            )

            blocked = self._run("next", project=project, home=home)
            payload = json.loads(blocked.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn(f"{package.resolve()}/references/brief.md", payload["check"]["reason"])
            self.assertNotIn("${workflowDir}", payload["instruction"])
            self.assertNotIn("${workflowDir}", payload["check"]["reason"])
            state_path = next(iter((project / ".workflow-harness" / "tasks").glob("*/state.json")))
            self.assertIn("workflow_dir", state_path.read_text(encoding="utf-8"))

    def test_workflowdir_works_in_command_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            package = self._package(
                project,
                command="python ${workflowDir}/scripts/check.py docs/requirements.md",
                human_request=None,
            )
            scripts = package / "scripts"
            scripts.mkdir()
            (scripts / "check.py").write_text(
                'from pathlib import Path\nimport sys\nif "ready" not in Path(sys.argv[1]).read_text(encoding="utf-8"):\n    raise SystemExit("not ready")\n',
                encoding="utf-8",
            )
            self._run("start", "workflowdir-demo", "--task", "Validate command path substitution", project=project, home=home)
            (project / "docs" / "requirements.md").parent.mkdir(parents=True, exist_ok=True)
            (project / "docs" / "requirements.md").write_text("wrong\n", encoding="utf-8")
            blocked = self._run("next", project=project, home=home)
            self.assertEqual(json.loads(blocked.stdout)["check"]["reason"], "not ready")

            (project / "docs" / "requirements.md").parent.mkdir(parents=True, exist_ok=True)
            (project / "docs" / "requirements.md").write_text("ready\n", encoding="utf-8")
            advanced = self._run("next", project=project, home=home)
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertEqual(json.loads(advanced.stdout)["status"], "done")

    def test_dedicated_workflow_script_gate_still_resolves_from_source_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = self._project(root)
            home = root / "home"
            home.mkdir()
            package = self._package(
                project,
                command='[ -f "${workflowDir}/references/brief.md" ]',
                human_request=None,
                script_gate=True,
            )
            scripts = package / "scripts"
            references = package / "references"
            scripts.mkdir()
            references.mkdir()
            (references / "brief.md").write_text("brief\n", encoding="utf-8")
            (scripts / "check.py").write_text(
                'from pathlib import Path\nimport sys\nif Path(sys.argv[1]).read_text(encoding="utf-8") != "script ready\\n":\n    raise SystemExit("script did not run")\n',
                encoding="utf-8",
            )

            self._run("start", "workflowdir-demo", "--task", "Validate script path substitution", project=project, home=home)
            (project / "docs" / "requirements.md").parent.mkdir(parents=True, exist_ok=True)
            (project / "docs" / "requirements.md").write_text("wrong\n", encoding="utf-8")

            blocked = self._run("next", project=project, home=home)
            self.assertEqual(json.loads(blocked.stdout)["check"]["gate"], "script")
            self.assertEqual(json.loads(blocked.stdout)["check"]["reason"], "script did not run")

            (project / "docs" / "requirements.md").write_text("script ready\n", encoding="utf-8")
            advanced = self._run("next", project=project, home=home)
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertEqual(json.loads(advanced.stdout)["status"], "done")
    def test_workflowdir_replacement_is_single_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            project.mkdir()
            workflow_home = root / "workflow" / "${artifact_name}"
            package = workflow_home / ".agents" / "workflows" / "workflowdir-demo"
            package.mkdir(parents=True)
            helpers.write_workflow(
                package,
                entry="preview",
                terminal="done",
                steps={
                    "preview": {
                        "title": "Preview",
                        "guide": "Read ${workflowDir}/references/brief.md.",
                        "gates": [],
                    },
                    "done": {"title": "Done", "guide": None, "gates": []},
                },
                transitions=[helpers.transition("preview", "done")],
            )
            (package / "references").mkdir()
            (package / "references" / "brief.md").write_text("brief\n", encoding="utf-8")

            env = {**os.environ, "HOME": str(workflow_home)}
            completed = helpers.run_wf(
                "start",
                "workflowdir-demo",
                "--task",
                "Check single pass replacement",
                cwd=project,
                env=env,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(
                payload["instruction"],
                f"Read {package.resolve() / 'references' / 'brief.md'}.",
            )


if __name__ == "__main__":
    unittest.main()
