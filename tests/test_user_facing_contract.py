import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import helpers


ROOT = Path(__file__).resolve().parents[1]


class UserFacingContractTest(unittest.TestCase):
    def test_skill_and_readme_do_not_reintroduce_legacy_arguments(self) -> None:
        skill = (ROOT / "skills" / "workflow-harness-run" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        examples = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")

        for document in (skill, readme, examples):
            with self.subTest(document=document):
                self.assertNotIn("--workflow", document)
                self.assertNotIn("--task-dir", document)
                self.assertNotIn("git+ssh", document)

    def test_skill_documents_the_agent_blind_runner_protocol(self) -> None:
        skill = (ROOT / "skills" / "workflow-harness-run" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn('awh start <workflow-alias> --task "<task-title>"', skill)
        self.assertIn("awh next", skill)
        self.assertIn(".workflow-harness/task.json", skill)
        self.assertTrue("5–120" in skill or "5-120" in skill)

        for status in ("active", "blocked", "done", "conflict", "error"):
            self.assertIn(status, skill)

        self.assertIn("不要自我宣布推进状态", skill)
        self.assertIn("不要把 `start` 当作二次触发或推进命令", skill)
        self.assertIn("`done` 后不要继续", skill)
        self.assertNotIn("python3 -m agent_workflow_harness", skill)
        self.assertIn("uv tool install --force .", skill)


    def test_runner_skill_documents_v2_start_inputs_and_route_errors(self) -> None:
        skill = (ROOT / "skills" / "workflow-harness-run" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn('[--var name=value]...', skill)
        self.assertIn("同一个变量不能在同一命令中重复", skill)
        self.assertIn("不要把它当作当前阶段的 `blocked` 修复说明", skill)
        self.assertIn("不要推断候选路由、条件、未来阶段或图结构", skill)
        self.assertNotIn("candidate edges", skill)
        self.assertNotIn("transition graph", skill)

    def test_runner_skill_keeps_input_preretrieval_domain_neutral(self) -> None:
        skill = (ROOT / "skills" / "workflow-harness-run" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## 任务输入准入", skill)
        self.assertIn("不负责解释业务语义", skill)
        self.assertNotIn("## 需求内容预取", skill)

    def test_creator_skill_is_manual_and_scope_safe(self) -> None:
        skill = (ROOT / "skills" / "workflow-harness-creator" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("disable-model-invocation: true", skill)
        self.assertIn("不随普通任务推进语言自动触发", skill)
        self.assertIn("<project>/.agents/workflows/<alias>/", skill)
        self.assertIn("只有用户明确要求跨项目复用", skill)
        self.assertIn("拒绝写入 built-in workflow catalog", skill)
        self.assertIn("等待用户批准", skill)
        self.assertIn("version: v2", skill)
        self.assertIn("condition_producers", skill)
        self.assertIn("awh validate <workflow-alias>", skill)
        self.assertIn("不修改 `.workflow-harness/`", skill)
        self.assertIn("docs/workflow-v2-authoring-guide.md", skill)

    def test_workflow_v2_authoring_guide_is_complete_and_linked(self) -> None:
        guide = (ROOT / "docs" / "workflow-v2-authoring-guide.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("[Workflow v2 authoring guide](docs/workflow-v2-authoring-guide.md)", readme)
        self.assertIn("Package layout", guide)
        self.assertIn("## Gate types", guide)
        self.assertIn("## Condition grammar and producers", guide)
        self.assertIn("## Explicit backedges", guide)
        self.assertIn("## Start inputs and resume semantics", guide)
        self.assertIn("## Copy-ready starter workflow", guide)
        self.assertIn("## Anti-patterns to avoid", guide)
        self.assertIn("self-loop", guide)
        self.assertIn("duplicate candidate targets", guide)
        self.assertIn("condition expression beyond single equality", guide)
        self.assertIn("## v1 compatibility", guide)
        self.assertIn("## Verify with `awh validate`", guide)

    def test_workflow_v2_starter_package_validates_at_cli_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            project = home / "project"
            project.mkdir()
            starter = ROOT / "examples" / "workflow-v2-starter" / "workflow.yaml"
            helpers.install_source_package(home, "workflow-v2-starter", workflow=starter)

            completed = helpers.run_wf(
                "validate",
                "workflow-v2-starter",
                cwd=project,
                env={**os.environ, "HOME": str(home)},
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload, {"status": "valid", "alias": "workflow-v2-starter"})


if __name__ == "__main__":
    unittest.main()
