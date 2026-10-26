from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class HumanHistoryTest(unittest.TestCase):
    """Human decisions must survive as inspectable runtime history."""

    def _setup(self, root: Path, *, cyclic: bool = False):
        project = root / "demo-project"
        project.mkdir()
        home = root / "home"
        if cyclic:
            workflow = helpers.write_workflow(
                home,
                entry="design",
                terminal="review",
                steps={
                    "design": {
                        "title": "Design",
                        "guide": "Read and think.",
                        "gates": [helpers.human_gate(
                            "requirements_confirmed_by_user",
                            "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                            ["docs/requirements.md"],
                        )],
                    },
                    "implementation": {
                        "title": "Implementation",
                        "guide": "Implement the design.",
                        "gates": [],
                    },
                    "review": {"title": "Review", "guide": None, "gates": []},
                },
                transitions=[
                    helpers.transition("design", "implementation"),
                    {"from": "design", "to": "review", "when": "finish == true"},
                    helpers.transition("implementation", "design"),
                ],
            )
        else:
            workflow = helpers.standard_workflow(
                home,
                design_gates=[
                    helpers.file_gate("requirements", "docs/requirements.md"),
                    helpers.human_gate(
                        "requirements_confirmed_by_user",
                        "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                        ["docs/requirements.md"],
                    ),
                ],
            )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)
        env = {**os.environ, "HOME": str(home)}
        extra_args = ["--var", "finish=false"] if cyclic else []
        started = helpers.run_wf(
            "start", "frontend-delivery", "--task", "Fix login timeout", *extra_args,
            cwd=project, env=env,
        )
        if started.returncode != 0:
            raise RuntimeError(started.stderr or started.stdout)
        return project, env

    def _history_path(self, project: Path) -> Path:
        pointer = json.loads((project / ".workflow-harness" / "task.json").read_text(encoding="utf-8"))
        task_dir = project / ".workflow-harness" / "tasks" / str(pointer["task_id"])
        return task_dir / "history.jsonl"

    def _events(self, path: Path) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_approval_and_transition_are_recorded_in_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, env = self._setup(root)
            (project / "docs").mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")
            helpers.run_wf("next", cwd=project, env=env)
            helpers.run_wf("approve", "--note", "需求已确认", cwd=project, env=env)
            helpers.run_wf("next", cwd=project, env=env)
            project = project

            events = self._events(self._history_path(project))
            human_events = [event for event in events if event["event"] == "human_decision"]
            self.assertEqual(len(human_events), 1)
            decision_event = human_events[0]
            self.assertEqual(decision_event["step"], "design")
            self.assertEqual(decision_event["gate"], "requirements_confirmed_by_user")
            self.assertEqual(decision_event["decision"], "approved")
            self.assertEqual(decision_event["note"], "需求已确认")
            self.assertIsInstance(decision_event["evidence_fingerprint"], str)

            success_events = [event for event in events if event["event"] == "success"]
            self.assertEqual(success_events, [
                {
                    "event": "success",
                    "from_step": "design",
                    "to_step": "implementation",
                    "human_gate": "requirements_confirmed_by_user",
                    "human_decision": "approved",
                    "human_decision_fingerprint": decision_event["evidence_fingerprint"],
                    "timestamp": success_events[0]["timestamp"],
                }
            ])

    def test_rejection_reason_is_recorded_in_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, env = self._setup(root)
            (project / "docs").mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")
            helpers.run_wf("next", cwd=project, env=env)
            helpers.run_wf(
                "reject", "--reason", "目标不清晰，需要补充边界", cwd=project, env=env
            )
            events = self._events(self._history_path(project))
            decision_event = next(event for event in events if event["event"] == "human_decision")
            self.assertEqual(decision_event["decision"], "rejected")
            self.assertEqual(decision_event["reason"], "目标不清晰，需要补充边界")

    def test_prior_approval_is_not_reused_when_a_step_repeats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, env = self._setup(root, cyclic=True)
            (project / "docs").mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")
            helpers.run_wf("next", cwd=project, env=env)
            helpers.run_wf("approve", cwd=project, env=env)
            helpers.run_wf("next", cwd=project, env=env)
            helpers.run_wf("next", cwd=project, env=env)

            revisited = helpers.run_wf("next", cwd=project, env=env)
            payload = json.loads(revisited.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["check"]["gate"], "requirements_confirmed_by_user")
            self.assertTrue(payload["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"))


if __name__ == "__main__":
    unittest.main()
