from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

import importlib.util

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO_ROOT / "agent_workflow_harness/workflows/frontend-delivery/resources/code_review_gate.py"
_spec = importlib.util.spec_from_file_location("code_review_gate", _SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Could not load the production CodeReview gate resource")
_code_review_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_code_review_gate)
validate_code_review_report = _code_review_gate.validate_code_review_report


class FrontendDeliveryCodeReviewGateTest(unittest.TestCase):
    """Validate the frontend delivery CodeReview gate module."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        workflow_path = repo_root / "agent_workflow_harness/workflows/frontend-delivery/workflow.yaml"
        gates = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))["steps"]["CodeReview"]["gates"]
        self.assertEqual(gates[0]["id"], "code_review_file")
        self.assertEqual(gates[1]["id"], "code_review_all_issues_fixed")
        self.assertEqual(gates[1]["type"], "workflow_script")
        self.assertEqual(gates[1]["script"], "resources/code_review_gate.py")
        self.assertEqual(gates[1]["project_args"], ["${taskDir}/code-review.md"])

    def test_code_review_template_is_shipped(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        template = repo_root / "agent_workflow_harness/workflows/frontend-delivery/resources/code-review.md"
        text = template.read_text(encoding="utf-8")
        self.assertTrue(template.is_file())
        self.assertIn("状态：已修复", text)
        self.assertIn("未修复问题数：0", text)

    def test_all_issues_fixed_passes(self) -> None:
        report = """# CodeReview
## 问题清单
### [P1] Real issue
- 现象：A real bug
- 修复：Fixed bug
- 验证：npm test passes
- 状态：已修复

## 结论
未修复问题数：0
"""
        with tempfile.TemporaryDirectory():
            validate_code_review_report(report)

    def test_issue_without_fixed_status_is_blocked(self) -> None:
        report = """# CodeReview
## 问题清单
### [P1] Real issue
- 现象：A real bug

## 结论
未修复问题数：0
"""
        with self.assertRaises(ValueError) as context:
            validate_code_review_report(report)
        self.assertIn("每个 CodeReview 问题都必须标记为 状态：已修复", str(context.exception))

    def test_open_issue_is_blocked(self) -> None:
        report = """# CodeReview
## 问题清单
### [P1] Real issue
- 状态：未修复

## 结论
未修复问题数：0
"""
        with self.assertRaises(ValueError) as context:
            validate_code_review_report(report)
        self.assertIn("每个 CodeReview 问题都必须标记为 状态：已修复", str(context.exception))

    def test_nonzero_unfixed_count_is_blocked(self) -> None:
        report = """# CodeReview
## 问题清单
### [P1] Real issue
- 状态：已修复

## 结论
未修复问题数：1
"""
        with self.assertRaises(ValueError) as context:
            validate_code_review_report(report)
        self.assertIn("未修复问题数必须为 0", str(context.exception))


if __name__ == "__main__":
    unittest.main()
