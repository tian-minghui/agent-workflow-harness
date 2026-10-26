"""Contract tests for the workflow-harness-creator skill's generic principles."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "workflow-harness-creator" / "SKILL.md"
REFERENCES = ROOT / "skills" / "workflow-harness-creator" / "references"


class WorkflowHarnessCreatorPrinciplesTest(unittest.TestCase):
    def test_skill_establishes_one_generic_authoring_protocol(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("都使用同一套创作协议", text)
        self.assertIn("不要按输入来源拆成不同模式", text)
        self.assertNotIn("skill-to-workflow", text)
        self.assertNotIn("description-to-workflow", text)
        self.assertNotIn("source-driven mode", text)
        self.assertNotIn("target-driven mode", text)

    def test_skill_links_the_methodology_references(self) -> None:
        for filename in (
            "workflow-authoring-contract.md",
            "artifact-typing.md",
            "gate-design-contract.md",
        ):
            path = REFERENCES / filename
            self.assertTrue(path.is_file(), path)
            self.assertIn(f"references/{filename}", SKILL.read_text(encoding="utf-8"))

    def test_authoring_contract_requires_contract_first_and_evidence_first(self) -> None:
        text = (REFERENCES / "workflow-authoring-contract.md").read_text(
            encoding="utf-8"
        )

        for marker in (
            "## 通用原则",
            "Contract first",
            "Evidence first",
            "No fabricated output",
            "Package is the product",
            "\n## 通用流程",
            "\n## 通用反模式",
            "\n## 完成判定",
        ):
            self.assertIn(marker, text)

    def test_artifact_typing_avoids_a_uniform_stage_file_model(self) -> None:
        text = (REFERENCES / "artifact-typing.md").read_text(encoding="utf-8")

        for marker in (
            "先判断阶段真实产生什么",
            "Markdown 判定",
            "JSON / YAML 判定",
            "条件产物",
            "可替换生成器",
            "\n## 通用禁止项",
        ):
            self.assertIn(marker, text)

    def test_gate_design_is_completion_first(self) -> None:
        text = (REFERENCES / "gate-design-contract.md").read_text(encoding="utf-8")

        for marker in (
            "这个阶段的真实完成条件",
            "`file_exists` 适用边界",
            "`workflow_script` 适用边界",
            "`human` 适用边界",
            "`condition_producers` 适用边界",
            "\n## Audit stage",
            "\n## 通用禁止项",
        ):
            self.assertIn(marker, text)

    def test_skill_forbids_fabricated_outputs(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("不默认“每个阶段都生成 stage Markdown”", text)
        self.assertIn("不用空正文模板填充不存在的产物", text)
        self.assertIn("不为路径不确定的产物硬造目录", text)
        self.assertIn("不绑定默认实现或固定模板", text)
        self.assertIn("awh validate <workflow-alias>", text)

class WorkflowCreatorClarificationProtocolTest(unittest.TestCase):
    def test_clarification_protocol_defines_blocking_questions(self) -> None:
        text = (REFERENCES / "clarification-protocol.md").read_text(encoding="utf-8")

        for marker in (
            "## 必须澄清的硬阻塞",
            "## 不需要澄清的情况",
            "## 澄清卡格式",
            "## 使用时机",
            "## 收到回答后",
            "不要继续创建 workflow 包文件",
        ):
            self.assertIn(marker, text)

    def test_skill_tells_user_to_ask_before_creation(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("遇到硬阻塞时先向用户澄清", text)
        self.assertIn("先发澄清卡", text)
        self.assertIn("不要继续创建或修改 workflow", text)
        self.assertIn("不要重复追问同一问题", text)


if __name__ == "__main__":
    unittest.main()
