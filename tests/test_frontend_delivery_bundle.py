from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from tests import helpers


class FrontendDeliveryWorkflowBundleTest(unittest.TestCase):
    """Directory package path for the built-in frontend-delivery workflow."""

    def _run(self, *args: str, project: Path, wf_home: Path):
        return helpers.run_wf(
            *args,
            cwd=project,
            env={**os.environ, "HOME": str(wf_home)},
        )

    def test_frontend_delivery_runs_end_to_end_from_unrelated_directory(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        workflow_package = repo_root / "agent_workflow_harness/workflows/frontend-delivery"
        workflow_data = yaml.safe_load(
            (workflow_package / "workflow.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(workflow_data["steps"]["CodeReview"]["gates"][1]["type"], "workflow_script")
        self.assertTrue((workflow_package / "resources/code_review_gate.py").is_file())
        self.assertTrue((workflow_package / "resources/code-review.md").is_file())

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "unrelated-project"
            project.mkdir()
            wf_home = root / "workflow-home"

            start = self._run("start", "frontend-delivery", "--task", "Use full workflow from outside directory", project=project, wf_home=wf_home)
            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertEqual(json.loads(start.stdout)["status"], "active")
            artifacts = helpers.active_artifact_dir(project)

            (artifacts / "requirements.md").write_text("# 需求\n目标：完成可交付的页面。\n", encoding="utf-8")
            (artifacts / "design.md").write_text("# 设计\n方案：使用项目内静态页面。\n", encoding="utf-8")
            (artifacts / "tasks.md").write_text("# 任务\n测试范围：核心状态机与表单交互。\n", encoding="utf-8")
            (artifacts / "implementation.md").write_text("# 实现\n记录核心实现决策。\n", encoding="utf-8")
            (artifacts / "test-report.md").write_text("npm test 通过\n", encoding="utf-8")
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
            (artifacts / "pr.md").write_text("# PR\nPR 信息已整理。\n", encoding="utf-8")
            (project / "package.json").write_text(
                '{"name":"external-workflow-demo","version":"1.0.0","scripts":{"test":"node -e \\"\\\""}}',
                encoding="utf-8",
            )
            (project / "index.html").write_text(
                "<!doctype html><html lang=\"zh-CN\"><body>ok</body></html>",
                encoding="utf-8",
            )

            approved_human_gates = 0
            for _ in range(20):
                advanced = self._run("next", project=project, wf_home=wf_home)
                payload = json.loads(advanced.stdout)

                if payload["status"] == "blocked" and payload["check"]["reason"].startswith(
                    "HUMAN_REVIEW_PENDING:"
                ):
                    approved_human_gates += 1
                    approved = self._run("approve", project=project, wf_home=wf_home)
                    self.assertEqual(approved.returncode, 1, approved.stderr)
                    continue

                self.assertEqual(advanced.returncode, 0, advanced.stderr)
                current_status = payload["status"]
                self.assertIn(current_status, {"active", "done"})
                if current_status == "done":
                    self.assertEqual(payload["task"]["title"], "Use full workflow from outside directory")
                    self.assertEqual(approved_human_gates, 3)
                    break
            else:
                self.fail("frontend-delivery did not reach done")

            tasks_dir = project / ".workflow-harness" / "tasks"
            task_dirs = list(tasks_dir.iterdir())
            self.assertEqual(len(task_dirs), 1)
            task_dir = task_dirs[0]
            state = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(
                Path(str(state["workflow_dir"])).resolve(),
                workflow_package.resolve(),
            )
            self.assertTrue(
                (workflow_package / "resources" / "code_review_gate.py").is_file()
            )
            self.assertTrue((workflow_package / "resources" / "code-review.md").is_file())
            self.assertFalse((task_dir / "workflow.snapshot.yaml").exists())
            self.assertFalse((task_dir / "workflow.package").exists())
            self.assertFalse((project / ".workflow-harness" / "task.json").exists())


if __name__ == "__main__":
    unittest.main()
