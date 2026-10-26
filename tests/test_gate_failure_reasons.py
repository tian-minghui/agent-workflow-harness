from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


class GateFailureReasonTest(unittest.TestCase):
    """Content gates must explain a missing keyword instead of failing silently."""

    def _workflow_paths(self) -> list[Path]:
        repo_root = Path(__file__).resolve().parents[1]
        return [
            repo_root / "agent_workflow_harness/workflows/frontend-delivery/workflow.yaml",
            repo_root / "agent_workflow_harness/workflows/meeting-summary/workflow.yaml",
        ]

    def test_grep_gates_explain_missing_keyword(self) -> None:
        expected = [
            ("${taskDir}/requirements.md", "目标"),
            ("${taskDir}/design.md", "方案"),
            ("${taskDir}/tasks.md", "测试"),
            ("${taskDir}/implementation.md", "实现"),
            ("${taskDir}/pr.md", "PR"),
            ("${taskDir}/meeting-brief.md", "主题"),
            ("${taskDir}/topics.md", "议题"),
            ("${taskDir}/conclusions.md", "结论"),
            ("${taskDir}/actions.md", "行动项"),
            ("${taskDir}/meeting-risks.md", "风险"),
            ("${taskDir}/meeting-summary.md", "纪要"),
        ]

        with self.subTest("all expected grep gates exist in every shipped workflow"):
            counts: dict[tuple[str, str], int] = {}
            for workflow_path in self._workflow_paths():
                workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
                for step in workflow["steps"].values():
                    for gate in step.get("gates", []):
                        command = gate.get("command", "")
                        match = re.search(r'grep -q "([^"]+)" (\S+)', command)
                        if match:
                            key = (match.group(2), match.group(1))
                            counts[key] = counts.get(key, 0) + 1

            for key in expected:
                self.assertEqual(counts.get(key, 0), 1, f"Missing content gate for {key}")
            self.assertSetEqual(set(counts.keys()), set(expected))

        for workflow_path in self._workflow_paths():
            workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
            for step_name, step in workflow["steps"].items():
                for gate in step.get("gates", []):
                    if gate.get("type") != "command":
                        continue

                    command = gate.get("command", "")
                    match = re.search(r'grep -q "([^"]+)" (\S+)', command)
                    if not match:
                        continue

                    keyword, doc_path = match.group(1), match.group(2)
                    payload = "No target keyword.\n"
                    reason = f"{doc_path} 中未找到关键字：{keyword}"

                    with tempfile.TemporaryDirectory() as temp_dir:
                        project_root = Path(temp_dir)
                        target = project_root / doc_path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(payload, encoding="utf-8")

                        result = subprocess.run(
                            command,
                            cwd=project_root,
                            shell=True,
                            text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        check=False,
                        )

                    self.assertEqual(
                        result.returncode,
                        1,
                        f"{step_name}/{gate['id']} should block when {doc_path} misses {keyword}",
                    )
                    self.assertIn(
                        reason,
                        result.stderr,
                        f"{step_name}/{gate['id']} did not explain its failure reason",
                    )
                    self.assertIn(
                        "grep -q",
                        command,
                        f"{step_name}/{gate['id']} is not a grep gate",
                    )


if __name__ == "__main__":
    unittest.main()
