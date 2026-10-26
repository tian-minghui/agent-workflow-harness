from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


class HumanDecisionCommandTest(unittest.TestCase):
    """Black-box checks for human decision commands."""

    def _setup(self, root: Path, *, file_gate: bool = True):
        project = root / "demo-project"
        project.mkdir()
        home = root / "home"
        design_gates: list[dict[str, object]] = []
        if file_gate:
            design_gates.append(helpers.file_gate("requirements", "docs/requirements.md"))
        design_gates.append(
            helpers.human_gate(
                "requirements_confirmed_by_user",
                "请确认当前目标、业务边界和验收标准是否符合你的真实预期。",
                ["docs/requirements.md"],
            )
        )
        workflow = helpers.standard_workflow(
            home,
            design_gates=design_gates,
            design_guide="Read and think.",
            implementation_guide="Implement the design.",
        )
        helpers.install_source_package(home, "frontend-delivery", workflow=workflow)
        env = {**os.environ, "HOME": str(home)}
        started = helpers.run_wf(
            "start", "frontend-delivery", "--task", "Fix login timeout",
            cwd=project, env=env,
        )
        if started.returncode != 0:
            raise RuntimeError(started.stderr or started.stdout)
        return project, home, env

    def _write_evidence(self, project: Path, text: str = "目标\n") -> None:
        path = project / "docs" / "requirements.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _run(self, *args: str, project: Path, env: dict[str, str]):
        return helpers.run_wf(*args, cwd=project, env=env)

    def test_approval_is_record_only_and_advances_next(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root, file_gate=False)
            self._write_evidence(project)
            pending = self._run("next", project=project, env=env)
            self.assertEqual(pending.returncode, 1, pending.stderr)
            self.assertTrue(json.loads(pending.stdout)["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"))

            approved = self._run("approve", "--note", "需求已确认", project=project, env=env)
            self.assertEqual(approved.returncode, 1, approved.stderr)
            self.assertTrue(json.loads(approved.stdout)["check"]["reason"].startswith("HUMAN_REVIEW_RECORDED:"))

            completed = self._run("next", project=project, env=env)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["instruction"], "Implement the design.")

    def test_approval_requires_ready_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            completed = self._run("approve", project=project, env=env)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("automatic", payload["reason"].lower())

    def test_rejection_is_sticky_until_evidence_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project)
            self._run("next", project=project, env=env)
            rejected = self._run(
                "reject", "--reason", "目标不清晰，需要补充边界", project=project, env=env
            )
            self.assertTrue(json.loads(rejected.stdout)["check"]["reason"].startswith("HUMAN_REVIEW_REJECTED:"))

            unchanged = self._run("next", project=project, env=env)
            reason = json.loads(unchanged.stdout)["check"]["reason"]
            self.assertTrue(reason.startswith("HUMAN_REVIEW_UNCHANGED:"))
            self.assertIn("目标不清晰，需要补充边界", reason)
            self.assertIn("awh approve", reason)
            self.assertIn("awh reject --reason", reason)

            self._write_evidence(project, "目标：Fix login timeout。\n")
            changed = self._run("next", project=project, env=env)
            changed_reason = json.loads(changed.stdout)["check"]["reason"]
            self.assertTrue(changed_reason.startswith("HUMAN_REVIEW_PENDING:"))
            self.assertIn("目标不清晰，需要补充边界", changed_reason)

    def test_rejected_evidence_cannot_be_reapproved_without_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project)
            self._run("next", project=project, env=env)
            self._run("reject", "--reason", "目标不清晰，需要补充边界", project=project, env=env)

            completed = self._run("approve", project=project, env=env)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("unchanged", payload["reason"].lower())

    def test_missing_approved_evidence_reads_as_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root, file_gate=False)
            self._write_evidence(project)
            self._run("next", project=project, env=env)
            self._run("approve", project=project, env=env)
            (project / "docs" / "requirements.md").unlink()

            blocked = self._run("next", project=project, env=env)
            reason = json.loads(blocked.stdout)["check"]["reason"]
            self.assertTrue(reason.startswith("HUMAN_APPROVAL_STALE:"))
            self.assertIn("awh approve", reason)
            self.assertIn("awh reject --reason", reason)

    def test_reject_reason_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project)
            self._run("next", project=project, env=env)

            completed = self._run(
                "reject", "--reason", "x" * 501, project=project, env=env
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("too long", payload["reason"])

    def test_rejection_on_changed_evidence_blocks_until_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root)
            self._write_evidence(project)
            self._run("next", project=project, env=env)
            self._run("reject", "--reason", "请补充兼容性要求", project=project, env=env)
            self._write_evidence(project, "目标：Fix login timeout；兼容性：Chrome。\n")

            blocked = self._run("next", project=project, env=env)
            self.assertTrue(json.loads(blocked.stdout)["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"))
            self._run("approve", project=project, env=env)
            advanced = self._run("next", project=project, env=env)
            self.assertEqual(json.loads(advanced.stdout)["status"], "active")

    def test_reject_cannot_record_before_an_automatic_gate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project, _, env = self._setup(root, file_gate=False)
            completed = self._run(
                "reject", "--reason", "证据文件缺失", project=project, env=env
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "error")
            self.assertIn("Human evidence is missing", payload["reason"])


if __name__ == "__main__":
    unittest.main()
