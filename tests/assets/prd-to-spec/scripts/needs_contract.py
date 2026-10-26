from pathlib import Path


def main() -> int:
    value = Path("evidence/contract.txt").read_text(encoding="utf-8").strip()
    print("true" if value == "cross-application" else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
