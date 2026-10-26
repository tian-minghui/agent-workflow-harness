from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import yaml

from tests import helpers


class FrontendDeliveryHumanGateTest(unittest.TestCase):
    """The built-in delivery workflow and runner skill understand human decisions."""

    def test_frontend_workflow_has_three_declared_human_gates(self) -> None:
        root = Path(__file__).resolve().parents[1]
        workflow_path = (
            root / "agent_workflow_harness/workflows/frontend-delivery/workflow.yaml"
        )
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

        human_gates = {
            step_name: gate
            for step_name, step in workflow["steps"].items()
            for gate in step.get("gates", [])
            if gate["type"] == "human"
        }

        self.assertEqual(set(human_gates), {"需求澄清", "方案设计", "提PR"})
        self.assertEqual(
            human_gates["需求澄清"]["evidence"], ["${taskDir}/requirements.md"]
        )
        self.assertEqual(human_gates["方案设计"]["evidence"], ["${taskDir}/design.md"])
        self.assertEqual(human_gates["提PR"]["evidence"], ["${taskDir}/pr.md"])
        for gate in human_gates.values():
            self.assertTrue(gate["request"].strip())

    def test_runner_skill_documents_human_decision_commands(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill = (root / "skills/workflow-harness-run/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("awh approve", skill)
        self.assertIn("awh reject --reason", skill)
        self.assertIn("HUMAN_REVIEW_PENDING", skill)
        self.assertIn("HUMAN_REVIEW_RECORDED", skill)
        self.assertIn("HUMAN_REVIEW_REJECTED", skill)
        self.assertIn("HUMAN_APPROVAL_STALE", skill)
        self.assertIn("HUMAN_REVIEW_UNCHANGED", skill)
        self.assertNotIn("waiting_human", skill)

    def test_frontend_delivery_runs_with_three_human_gates(self) -> None:
        root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project = workspace / "project"
            project.mkdir()
            wf_home = workspace / "workflow-home"
            env = {**os.environ, "HOME": str(wf_home)}

            start = helpers.run_wf(
                "start", "frontend-delivery", "--task", "Run human-reviewed frontend delivery",
                cwd=project, env=env,
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            artifacts = helpers.active_artifact_dir(project)

            (artifacts / "requirements.md").write_text(
                "# 需求\n目标：完成可交付的页面。\n", encoding="utf-8"
            )
            (artifacts / "design.md").write_text(
                "# 设计\n方案：使用项目内静态页面。\n", encoding="utf-8"
            )
            (artifacts / "tasks.md").write_text(
                "# 任务\n测试范围：核心交互。\n", encoding="utf-8"
            )
            (artifacts / "implementation.md").write_text(
                "# 实现\n记录核心实现决策。\n", encoding="utf-8"
            )
            (artifacts / "test-report.md").write_text(
                "npm test 通过\n", encoding="utf-8"
            )
            (artifacts / "code-review.md").write_text(
                """# CodeReview
## 问题清单
## 结论
- 发现问题数：0
- 已修复问题数：0
- 未修复问题数：0
""",
                encoding="utf-8",
            )
            (artifacts / "pr.md").write_text(
                "# PR\nPR 信息已整理。\n", encoding="utf-8"
            )
            (project / "package.json").write_text(
                '{"name":"human-gate-demo","version":"1.0.0","scripts":{"test":"node -e \\"\\\""}}',
                encoding="utf-8",
            )

            approved_count = 0
            for _ in range(20):
                result = helpers.run_wf("next", cwd=project, env=env)
                payload = json.loads(result.stdout)

                if payload["status"] == "blocked" and payload["check"]["reason"].startswith("HUMAN_REVIEW_PENDING:"):
                    approved_count += 1
                    approved = helpers.run_wf("approve", cwd=project, env=env)
                    self.assertEqual(approved.returncode, 1, approved.stderr)
                    continue

                self.assertEqual(result.returncode, 0, result.stderr)
                if payload["status"] == "done":
                    self.assertEqual(approved_count, 3)
                    break
            else:
                self.fail("frontend-delivery did not finish with three human approvals")


if __name__ == "__main__":
    unittest.main()
