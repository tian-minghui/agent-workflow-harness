from pathlib import Path


def main() -> int:
    value = Path("evidence/routing.txt").read_text(encoding="utf-8").strip()
    print("true" if value == "incomplete" else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
