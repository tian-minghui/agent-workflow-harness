from __future__ import annotations

import re
import sys
from pathlib import Path

ISSUE_PATTERN = re.compile(r"^###\s+\[P[0-3]\]\s+.+$", re.MULTILINE)
FIXED_STATUS_PATTERN = re.compile(r"^[-*]\s*状态：已修复\s*$", re.MULTILINE)
UNFIXED_SUMMARY = "未修复问题数：0"


def validate_code_review_report(report: str) -> None:
    if UNFIXED_SUMMARY not in report:
        raise ValueError("CodeReview 报告中未修复问题数必须为 0")

    issues = ISSUE_PATTERN.findall(report)
    fixed = FIXED_STATUS_PATTERN.findall(report)
    if len(issues) != len(fixed):
        raise ValueError("每个 CodeReview 问题都必须标记为 状态：已修复")

    if "状态：未修复" in report:
        raise ValueError("CodeReview 报告存在未修复问题")


def main() -> int:
    report_path = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/code-review.md")
    if not report_path.is_file():
        print(f"{report_path} 不存在", file=sys.stderr)
        return 1
    report = report_path.read_text(encoding="utf-8")
    try:
        validate_code_review_report(report)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
