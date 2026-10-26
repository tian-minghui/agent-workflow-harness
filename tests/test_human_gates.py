from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class HumanGateTest(unittest.TestCase):
    """Black-box behavior for human confirmation gates."""

    def _project(self, root: Path) -> tuple[Path, Path, dict[str, str]]:
        project = root / "demo-project"
        project.mkdir()
        wf_home = root / "workflow-home"
        env = {**os.environ, "HOME": str(wf_home)}
        return project, wf_home, env

    def _workflow(self, root: Path, design_gates: list[dict[str, object]]) -> Path:
        workflow = helpers.standard_workflow(
            root,
            design_gates=design_gates,
            design_guide="Read and think.",
            implementation_guide="Implement the design.",
        )
        helpers.install_source_package(root, "frontend-delivery", workflow=workflow)
        return workflow

    def _start(self, project: Path, wf_home: Path, title: str = "Fix login timeout"):
        return helpers.run_wf(
            "start", "frontend-delivery", "--task", title,
            cwd=project, env={**os.environ, "HOME": str(wf_home)},
        )

    def test_missing_evidence_stays_a_pending_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            self._workflow(
                wf_home,
                [
                    helpers.human_gate(
                        "requirements_confirmed_by_user",
                        "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                        ["docs/requirements.md"],
                    )
                ],
            )
            self._start(project, wf_home)

            blocked = helpers.run_wf(
                "next", cwd=project, env={**os.environ, "HOME": str(wf_home)}
            )

            payload = json.loads(blocked.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertTrue(payload["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"))

    def test_terminal_step_cannot_contain_a_human_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            workflow = helpers.write_workflow(
                wf_home,
                entry="design",
                terminal="done",
                steps={
                    "design": {"title": "Design", "guide": "Read and think.", "gates": []},
                    "done": {
                        "title": "Done",
                        "guide": None,
                        "gates": [helpers.human_gate("bad_gate", "请确认。", ["docs/requirements.md"])],
                    },
                },
                transitions=[helpers.transition("design", "done")],
            )
            helpers.install_source_package(wf_home, "frontend-delivery", workflow=workflow)

            completed = self._start(project, wf_home)

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")

    def test_duplicate_evidence_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            workflow = helpers.write_workflow(
                wf_home,
                entry="design",
                terminal="done",
                steps={
                    "design": {
                        "title": "Design",
                        "guide": "Read and think.",
                        "gates": [helpers.human_gate(
                            "requirements_confirmed_by_user",
                            "请确认需求。",
                            ["docs/requirements.md", "./docs/requirements.md"],
                        )],
                    },
                    "done": {"title": "Done", "guide": None, "gates": []},
                },
                transitions=[helpers.transition("design", "done")],
            )
            helpers.install_source_package(wf_home, "frontend-delivery", workflow=workflow)

            completed = self._start(project, wf_home)

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")

    def test_pending_human_gate_blocks_with_stable_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            self._workflow(
                wf_home,
                [
                    helpers.file_gate("requirements", "docs/requirements.md"),
                    helpers.human_gate(
                        "requirements_confirmed_by_user",
                        "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                        ["docs/requirements.md"],
                    ),
                ],
            )
            completed = self._start(project, wf_home)
            self.assertEqual(completed.returncode, 0, completed.stderr)

            (project / "docs").mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")

            blocked = helpers.run_wf(
                "next", cwd=project, env={**os.environ, "HOME": str(wf_home)}
            )

            self.assertEqual(blocked.returncode, 1, blocked.stderr)
            payload = json.loads(blocked.stdout)
            self.assertEqual(payload["status"], "blocked")
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
            self.assertEqual(payload["instruction"], "Read and think.")
            self.assertEqual(payload["check"]["gate"], "requirements_confirmed_by_user")
            self.assertTrue(payload["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"))
            self.assertIn("请确认当前目标、业务边界和验收标准", payload["check"]["reason"])
            self.assertIn("docs/requirements.md", payload["check"]["reason"])

    def test_human_gate_runs_after_automatic_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            self._workflow(
                wf_home,
                [
                    helpers.file_gate("requirements", "docs/requirements.md"),
                    helpers.human_gate(
                        "requirements_confirmed_by_user", "请确认需求。", ["docs/requirements.md"]
                    ),
                ],
            )
            self._start(project, wf_home)

            blocked = helpers.run_wf(
                "next", cwd=project, env={**os.environ, "HOME": str(wf_home)}
            )

            payload = json.loads(blocked.stdout)
            self.assertEqual(payload["check"]["gate"], "requirements")
            self.assertEqual(payload["check"]["reason"], "docs/requirements.md does not exist")

    def test_invalid_human_gate_is_rejected_at_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            self._workflow(
                wf_home,
                [
                    {
                        "id": "bad_human",
                        "type": "human",
                        "evidence": ["docs/requirements.md"],
                    }
                ],
            )

            completed = self._start(project, wf_home)

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["reason"], "Workflow definition is invalid or incomplete")

    def test_unsafe_and_empty_evidence_paths_are_rejected(self) -> None:
        invalid_evidence = [
            None,
            [],
            ["/tmp/docs.txt"],
            ["../docs.txt"],
        ]

        for evidence in invalid_evidence:
            with self.subTest(evidence=evidence), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                project, wf_home, _ = self._project(root)
                gate = {
                    "id": "human_gate",
                    "type": "human",
                    "request": "请确认需求。",
                }
                if evidence is not None:
                    gate["evidence"] = evidence
                workflow = helpers.write_workflow(
                    wf_home,
                    entry="design",
                    terminal="done",
                    steps={
                        "design": {
                            "title": "Design",
                            "guide": "Read and think.",
                            "gates": [gate],
                        },
                        "done": {"title": "Done", "guide": None, "gates": []},
                    },
                    transitions=[helpers.transition("design", "done")],
                )
                helpers.install_source_package(wf_home, "frontend-delivery", workflow=workflow)

                completed = self._start(project, wf_home)

                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "error")

    def test_request_length_and_evidence_count_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            workflow = helpers.write_workflow(
                wf_home,
                entry="design",
                terminal="done",
                steps={
                    "design": {
                        "title": "Design",
                        "guide": "Read and think.",
                        "gates": [{
                            "id": "human_gate",
                            "type": "human",
                            "request": "x" * 301,
                            "evidence": [f"docs/file{i}.md" for i in range(6)],
                        }],
                    },
                    "done": {"title": "Done", "guide": None, "gates": []},
                },
                transitions=[helpers.transition("design", "done")],
            )
            helpers.install_source_package(wf_home, "frontend-delivery", workflow=workflow)

            completed = self._start(project, wf_home)

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")

    def test_request_with_control_characters_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            workflow = helpers.write_workflow(
                wf_home,
                entry="design",
                terminal="done",
                steps={
                    "design": {
                        "title": "Design",
                        "guide": "Read and think.",
                        "gates": [{
                            "id": "human_gate",
                            "type": "human",
                            "request": "请确认需求。\x7f",
                            "evidence": ["docs/requirements.md"],
                        }],
                    },
                    "done": {"title": "Done", "guide": None, "gates": []},
                },
                transitions=[helpers.transition("design", "done")],
            )
            helpers.install_source_package(wf_home, "frontend-delivery", workflow=workflow)

            completed = self._start(project, wf_home)

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")

    def test_missing_evidence_reason_does_not_request_decision_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            self._workflow(
                wf_home,
                [
                    helpers.human_gate(
                        "requirements_confirmed_by_user",
                        "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                        ["docs/requirements.md"],
                    )
                ],
            )
            self._start(project, wf_home)

            completed = helpers.run_wf(
                "next", cwd=project, env={**os.environ, "HOME": str(wf_home)}
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertTrue(payload["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"))
            self.assertIn("请先创建证据文件", payload["check"]["reason"])
            self.assertNotIn("awh approve", payload["check"]["reason"])
            self.assertNotIn("awh reject --reason", payload["check"]["reason"])

    def test_relative_evidence_paths_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            self._workflow(
                wf_home,
                [
                    {
                        "id": "human",
                        "type": "human",
                        "request": "请确认",
                        "evidence": ["./docs/requirements.md"],
                    }
                ],
            )

            completed = self._start(project, wf_home)

            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_multiple_human_gates_in_one_step_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, wf_home, _ = self._project(root)
            workflow = self._workflow(
                wf_home,
                [
                    helpers.human_gate("one", "请确认需求。", ["docs/requirements.md"]),
                    helpers.human_gate("two", "请确认方案。", ["docs/design.md"]),
                ],
            )

            completed = self._start(project, wf_home)

            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)["status"], "error")


if __name__ == "__main__":
    unittest.main()
