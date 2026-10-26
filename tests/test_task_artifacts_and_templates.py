from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class TaskArtifactDirectoryTest(unittest.TestCase):
    """Task-scoped business artifacts and the template variables that locate them."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.project = self.root / "project"
        self.home = self.root / "home"
        self.project.mkdir()
        self.home.mkdir()

    def _install(self, alias: str, content: str) -> Path:
        package = self.home / ".agents" / "workflows" / alias
        package.mkdir(parents=True, exist_ok=True)
        (package / "workflow.yaml").write_text(content, encoding="utf-8")
        return package

    def _run(self, *args: str):
        return helpers.run_wf(
            *args,
            cwd=self.project,
            env={**os.environ, "HOME": str(self.home)},
        )

    def test_state_without_artifact_dir_is_rejected_without_repair(self) -> None:
        workflow = helpers.standard_workflow(self.home)
        helpers.install_source_package(self.home, "artifact-demo", workflow=workflow)
        self._run("start", "artifact-demo", "--task", "Inspect broken state")

        state_path = self.project / ".workflow-harness" / "tasks" / str(
            helpers.active_state(self.project)["task_id"]
        ) / "state.json"
        state = helpers.active_state(self.project)
        del state["artifact_dir"]
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        completed = self._run("next")
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(payload["status"], "error")
        self.assertIn("task state is invalid or unreadable", payload["reason"])
        self.assertEqual(
            state_path.read_text(encoding="utf-8"),
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        )

    def test_task_title_remains_natural_english_while_the_slug_is_safe(self) -> None:
        workflow = helpers.standard_workflow(
            self.home,
            design_gates=[helpers.file_gate("requirements", "${taskDir}/requirements.md")],
        )
        helpers.install_source_package(self.home, "artifact-demo", workflow=workflow)

        completed = self._run(
            "start", "artifact-demo", "--task", "Fix Login Timeout"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = helpers.active_state(self.project)
        task_id = str(state["task_id"])
        expected_artifact_dir = (
            ".workflow-harness/task-artifacts/"
            f"fix-login-timeout-{task_id}"
        )
        self.assertEqual(state["artifact_dir"], expected_artifact_dir)
        artifact_path = self.project / expected_artifact_dir
        self.assertTrue(artifact_path.is_dir())

        requirement = artifact_path / "requirements.md"
        requirement.write_text("Goal: recover from timeout\n", encoding="utf-8")
        advanced = self._run("next")
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertEqual(json.loads(advanced.stdout)["status"], "active")
        completed_run = self._run("next")
        self.assertEqual(completed_run.returncode, 0, completed_run.stderr)
        self.assertEqual(json.loads(completed_run.stdout)["status"], "done")
        self.assertFalse((self.project / ".workflow-harness" / "task.json").exists())
        self.assertTrue(artifact_path.is_dir())
        self.assertTrue(requirement.is_file())

    def test_non_english_or_slugless_titles_are_rejected_without_runtime(self) -> None:
        workflow = helpers.standard_workflow(self.home)
        helpers.install_source_package(self.home, "artifact-demo", workflow=workflow)

        for title in ("修复登录超时", " - - - ", "Implement user profile export!"):
            with self.subTest(title=title):
                completed = self._run("start", "artifact-demo", "--task", title)
                payload = json.loads(completed.stdout)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(payload["status"], "error")
                self.assertIn(
                    "Task title must be a natural English line",
                    payload["reason"],
                )
                self.assertFalse((self.project / ".workflow-harness").exists())

    def test_task_dir_and_start_input_substitute_in_instruction_and_gate(
        self,
    ) -> None:
        self._install(
            "template-demo",
            """version: v2
entry: draft
terminal: done
steps:
  draft:
    title: Draft
    guide: "Write ${taskDir}/${artifact_name}.md with ${artifact_name}."
    gates:
      - id: output
        type: file_exists
        path: "${taskDir}/${artifact_name}.md"
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
""",
        )
        completed = self._run(
            "start",
            "template-demo",
            "--task",
            "Implement template substitution",
            "--var",
            "artifact_name=requirements",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = helpers.active_state(self.project)
        expected = f"Write {state['artifact_dir']}/requirements.md with requirements."
        self.assertEqual(json.loads(completed.stdout)["instruction"], expected)

        artifact = self.project / str(state["artifact_dir"]) / "requirements.md"
        artifact.write_text("ready\n", encoding="utf-8")
        advanced = self._run("next")
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertEqual(json.loads(advanced.stdout)["status"], "done")

    def test_missing_template_start_input_is_an_error_before_task_creation(self) -> None:
        self._install(
            "missing-input",
            """version: v2
entry: draft
terminal: done
steps:
  draft:
    title: Draft
    guide: "Write ${taskDir}/${artifact_name}.md."
    gates: []
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
""",
        )
        completed = self._run("start", "missing-input", "--task", "Use helper input")
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(payload["status"], "error")
        self.assertIn("artifact_name", payload["reason"])
        self.assertFalse((self.project / ".workflow-harness").exists())

    def test_validate_rejects_malformed_template_names_in_commands(self) -> None:
        self._install(
            "bad-command-template",
            """version: v2
entry: draft
terminal: done
steps:
  draft:
    title: Draft
    guide: "Write the artifact."
    gates:
      - id: command
        type: command
        command: "echo ${ artifact_name }"
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
""",
        )
        completed = self._run("validate", "bad-command-template")
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("gate command command: invalid template variable", payload["reason"])

    def test_validate_rejects_malformed_template_variable_names(self) -> None:
        self._install(
            "bad-template",
            """version: v2
entry: draft
terminal: done
steps:
  draft:
    title: Draft
    guide: "Use ${ artifact_name }."
    gates: []
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
""",
        )
        completed = self._run("validate", "bad-template")
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("invalid template variable", payload["reason"])
        self.assertFalse((self.project / ".workflow-harness").exists())


if __name__ == "__main__":
    unittest.main()
