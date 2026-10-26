from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "docs/workflow-validation/benchmarks/runner.py"
STATIC_SKILL = ROOT / "docs/workflow-validation/skills/static-step.md"


class ThreeCaseBenchmarkTest(unittest.TestCase):
    def run_benchmark(self, root: Path):
        env = {
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": root.as_posix(),
            "PYTHONPATH": ROOT.as_posix(),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        return subprocess.run(
            [sys.executable, BENCH.as_posix(), "--root", root.as_posix()],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def test_static_skill_declares_full_process_and_gates(self):
        self.assertTrue(STATIC_SKILL.is_file(), "static skill prompt must exist")
        text = STATIC_SKILL.read_text(encoding="utf-8")
        for keyword in ("Step 1", "Step 2", "Step 3", "npm test", "must pass"):
            self.assertIn(keyword, text)

    def test_benchmark_produces_case_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.run_benchmark(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            for relative in (
                "case-a/results/summary.json",
                "case-b/results/summary.json",
                "case-c/results/summary.json",
                "REPORT.json",
            ):
                self.assertTrue((root / relative).is_file(), relative)

            case_a = json.loads((root / "case-a/results/summary.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(case_a["repetitions"], 3)
            self.assertFalse(any(r["harness_false_complete"] for r in case_a["runs"]))
            self.assertTrue(any(r["static_declared_complete_without_requirement"] for r in case_a["runs"]))

            case_b = json.loads((root / "case-b/results/summary.json").read_text(encoding="utf-8"))
            self.assertFalse(any(r["harness_false_complete"] for r in case_b["pass_runs"] + case_b["fail_runs"] + case_b["repair_runs"]))
            self.assertEqual(case_b["pass_runs"][0]["harness_done"], True)
            self.assertEqual(case_b["fail_runs"][0]["harness_final_status"] == "done", False)

            case_c = json.loads((root / "case-c/results/summary.json").read_text(encoding="utf-8"))
            self.assertEqual(case_c["mode_harness"]["calls"], 3)
            self.assertEqual(case_c["mode_static"]["calls"], 3)
            self.assertLess(
                case_c["mode_harness"]["cumulative_input"],
                case_c["mode_static"]["cumulative_input"],
                "harness work-order input should stay smaller than full static prompt",
            )

            report = json.loads((root / "REPORT.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["cases"]), 3)
            self.assertIn(report["overall_claim"], {"demonstrated", "not demonstrated"})


if __name__ == "__main__":
    unittest.main()
