from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class ProjectLocalRuntimeTest(unittest.TestCase):
    """The project-local pointer/state/history tuple is authoritative and closed."""

    def _project(self, root: Path) -> tuple[Path, Path]:
        project = root / "demo-project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        return project, root / "home"

    def _package(self, root: Path, alias: str = "runtime-demo") -> Path:
        package = root / ".agents" / "workflows" / alias
        package.mkdir(parents=True, exist_ok=True)
        helpers.standard_workflow(
            package,
            design_gates=[helpers.file_gate("requirements", "docs/requirements.md")],
        )
        return package

    def _env(self, home: Path) -> dict[str, str]:
        return {**os.environ, "HOME": str(home)}

    def _start(self, project: Path, home: Path, title: str = "Complete runtime refactor"):
        return helpers.run_wf(
            "start",
            "runtime-demo",
            "--task",
            title,
            cwd=project,
            env=self._env(home),
        )

    def _next(self, project: Path, home: Path):
        return helpers.run_wf("next", cwd=project, env=self._env(home))

    def _runtime(self, project: Path) -> tuple[Path, Path, Path]:
        runtime_dir = project / ".workflow-harness"
        pointer_path = runtime_dir / "task.json"
        if pointer_path.exists():
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            task_dir = runtime_dir / "tasks" / str(pointer["task_id"])
        else:
            task_dir = next(iter((runtime_dir / "tasks").iterdir()))
        return pointer_path, task_dir, task_dir / "state.json"

    def test_start_creates_minimal_pointer_and_authoritative_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            package = self._package(project)
            home.mkdir()

            start = self._start(project, home)
            self.assertEqual(start.returncode, 0, start.stderr)
            pointer_path, task_dir, state_path = self._runtime(project)
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            state = json.loads(state_path.read_text(encoding="utf-8"))

            self.assertEqual(
                set(pointer),
                {"schema", "task_id", "workflow_alias", "title"},
            )
            self.assertEqual(
                set(state),
                {
                    "schema",
                    "task_id",
                    "workflow_alias",
                    "title",
                    "step",
                    "workflow_dir",
                    "artifact_dir",
                    "workflow_yaml_sha256",
                    "inputs",
                    "facts",
                    "visited_steps",
                    "backedge_counts",
                },
            )
            self.assertEqual(state["step"], "design")
            self.assertEqual(state["inputs"], {})
            self.assertEqual(state["facts"], {})
            self.assertEqual(state["visited_steps"], ["design"])
            self.assertEqual(state["backedge_counts"], {})
            self.assertEqual(Path(state["workflow_dir"]).resolve(), package.resolve())
            self.assertIn("\n", state_path.read_text(encoding="utf-8"))
            self.assertEqual(set(task_dir.iterdir()), {task_dir / "state.json", task_dir / "history.jsonl"})

    def test_next_without_pointer_does_not_auto_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()

            completed = self._next(project, home)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["reason"], "No active workflow task")
            self.assertFalse((project / ".workflow-harness" / "task.json").exists())
            self.assertFalse((project / ".workflow-harness" / "tasks").exists())

    def test_pointer_to_missing_task_directory_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            self._package(project)
            self._start(project, home)
            _, task_dir, _ = self._runtime(project)

            shutil.rmtree(task_dir)

            completed = self._next(project, home)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("active workflow task directory is missing", payload["reason"].lower())

    def test_pointer_and_state_identity_mismatch_is_an_error(self) -> None:
        for field, value in (
            ("task_id", "task-" + "1" * 32),
            ("workflow_alias", "other-demo"),
            ("title", "Different task title"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                project, home = self._project(root)
                home.mkdir()
                self._package(project)
                self._start(project, home)
                _, task_dir, state_path = self._runtime(project)
                state = json.loads(state_path.read_text(encoding="utf-8"))
                task_id = str(state["task_id"])
                state[field] = value
                if field == "task_id":
                    state["artifact_dir"] = str(state["artifact_dir"]).replace(
                        task_id, str(value)
                    )
                elif field == "title":
                    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")[:64]
                    state["artifact_dir"] = (
                        ".workflow-harness/task-artifacts/"
                        f"{slug}-{task_id}"
                    )
                (project / str(state["artifact_dir"])).mkdir(parents=True, exist_ok=True)
                state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

                completed = self._next(project, home)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "error")
                self.assertIn("identity mismatch", payload["reason"].lower())
                history = [
                    json.loads(line)
                    for line in (task_dir / "history.jsonl").read_text(encoding="utf-8").splitlines()
                ]
                self.assertEqual(history[-1]["event"], "error")
                self.assertIn("identity mismatch", history[-1]["reason"])

    def test_start_resume_and_conflict_semantics_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            self._package(project)

            first = self._start(project, home)
            self.assertEqual(first.returncode, 0, first.stderr)
            resumed = self._start(project, home, title="Complete  runtime refactor")
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(json.loads(first.stdout), json.loads(resumed.stdout))
            tasks = list((project / ".workflow-harness" / "tasks").iterdir())
            self.assertEqual(len(tasks), 1)

            conflict = self._start(project, home, title="Different task title")
            self.assertEqual(conflict.returncode, 1)
            payload = json.loads(conflict.stdout)
            self.assertEqual(payload["status"], "conflict")
            self.assertEqual(payload["active_task"], {"title": "Complete runtime refactor"})
            self.assertEqual(len(list((project / ".workflow-harness" / "tasks").iterdir())), 1)

    def test_done_removes_pointer_but_preserves_task_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            self._package(project)
            self._start(project, home)
            _, task_dir, _ = self._runtime(project)
            (project / "docs" / "requirements.md").parent.mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")

            first = self._next(project, home)
            self.assertEqual(first.returncode, 0, first.stderr)
            done = self._next(project, home)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(done.stdout)["status"], "done")

            self.assertFalse((project / ".workflow-harness" / "task.json").exists())
            self.assertTrue(task_dir.is_dir())
            state = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["step"], "done")

    def test_workflow_definition_drift_is_an_error_for_next_and_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            package = self._package(project)
            self._start(project, home)
            workflow_path = package / "workflow.yaml"
            original = workflow_path.read_text(encoding="utf-8")
            workflow_path.write_text(original.replace("Read and think.", "Changed graph."), encoding="utf-8")

            next_result = self._next(project, home)
            payload = json.loads(next_result.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Workflow definition source changed", payload["reason"])

            start_result = self._start(project, home)
            payload = json.loads(start_result.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Workflow definition source changed", payload["reason"])

    def test_non_definition_asset_drift_does_not_break_the_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            package = self._package(project)
            reference = package / "references" / "notes.md"
            reference.parent.mkdir()
            reference.write_text("old note\n", encoding="utf-8")
            self._start(project, home)
            reference.write_text("new note\n", encoding="utf-8")

            advanced = self._next(project, home)
            self.assertEqual(advanced.returncode, 1)
            payload = json.loads(advanced.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["check"]["reason"], "docs/requirements.md does not exist")

    def test_conflict_cannot_mask_broken_active_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            self._package(project)
            self._start(project, home)
            _, task_dir, _ = self._runtime(project)
            shutil.rmtree(task_dir)

            conflict_attempt = self._start(project, home, title="Different task title")
            payload = json.loads(conflict_attempt.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("active workflow task directory is missing", payload["reason"].lower())

    def test_source_drift_scopes_to_start_and_next_not_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            package = self._package(project)
            helpers.standard_workflow(
                package,
                design_gates=[
                    helpers.file_gate("requirements", "docs/requirements.md"),
                    helpers.human_gate(
                        "confirmation",
                        "确认运行时漂移决策",
                        ["docs/requirements.md"],
                    ),
                ],
            )
            definition_path = package / "workflow.yaml"
            self._start(project, home)
            evidence = project / "docs" / "requirements.md"
            evidence.parent.mkdir(parents=True)
            evidence.write_text("目标\n", encoding="utf-8")
            pending = self._next(project, home)
            self.assertEqual(json.loads(pending.stdout)["status"], "blocked")

            definition_path.write_text(
                definition_path.read_text(encoding="utf-8").replace(
                    "Read and think.",
                    "Guide changed but graph not advanced.",
                ),
                encoding="utf-8",
            )
            decision = helpers.run_wf("approve", cwd=project, env=self._env(home))
            decision_payload = json.loads(decision.stdout)
            self.assertEqual(decision_payload["status"], "blocked")
            self.assertTrue(
                decision_payload["check"]["reason"].startswith("HUMAN_REVIEW_RECORDED:")
            )

            blocked = self._next(project, home)
            self.assertEqual(json.loads(blocked.stdout)["status"], "error")

    def test_history_records_meaningful_outcomes_without_rebuilding_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, home = self._project(root)
            home.mkdir()
            self._package(project)
            self._start(project, home)

            blocked = self._next(project, home)
            self.assertEqual(blocked.returncode, 1)
            (project / "docs" / "requirements.md").parent.mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")
            self._next(project, home)
            self._next(project, home)

            _, task_dir, state_path = self._runtime(project)
            self.assertFalse((project / ".workflow-harness" / "task.json").exists())
            history = [
                json.loads(line)
                for line in (task_dir / "history.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [event["event"] for event in history],
                ["started", "blocked", "success", "success", "done"],
            )
            (task_dir / "history.jsonl").write_text("", encoding="utf-8")
            self.assertTrue(state_path.is_file())


if __name__ == "__main__":
    unittest.main()
