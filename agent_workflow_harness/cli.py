from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from agent_workflow_harness.runtime import (
    WorkflowCommandError,
    record_human_decision,
    run_next,
    start_workflow,
    validate_workflow_definition,
)


def _print_workflow_error(error: WorkflowCommandError) -> None:
    payload = {"status": error.status, "reason": error.reason}
    if error.active_task_title:
        payload["active_task"] = {"title": error.active_task_title}
    if error.hint:
        payload["hint"] = error.hint
    print(json.dumps(payload, ensure_ascii=False), end="")


class AgentWorkflowParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        print(
            json.dumps(
                {
                    "status": "error",
                    "reason": "Invalid command arguments",
                    "hint": "Run awh --help",
                }
            ),
            end="",
        )
        self.exit(2)


def _run_agent_blind_next(project_path: str | None = None) -> int:
    try:
        result = run_next(project_path)
    except WorkflowCommandError as error:
        _print_workflow_error(error)
        return 1
    except OSError:
        print(
            json.dumps(
                {
                    "status": "error",
                    "reason": "Workflow storage could not be read or written",
                }
            ),
            end="",
        )
        return 1

    payload = {
        "status": result.status,
        "task": result.task.payload,
    }
    if result.status in {"active", "blocked"}:
        payload["instruction"] = result.instruction
    if result.status == "blocked":
        payload["check"] = {"gate": result.gate, "reason": result.reason}
    print(json.dumps(payload, ensure_ascii=False), end="")
    return 1 if result.status == "blocked" else 0

def command_start(args: argparse.Namespace) -> int:
    try:
        result = start_workflow(args.alias, args.task, raw_variables=args.variables)
    except WorkflowCommandError as error:
        _print_workflow_error(error)
        return 1
    except OSError:
        print(
            json.dumps(
                {
                    "status": "error",
                    "reason": "Workflow storage could not be read or written",
                }
            ),
            end="",
        )
        return 1

    print(
        json.dumps(
            {
                "status": result.status,
                "task": result.task.payload,
                "instruction": result.instruction,
            },
            ensure_ascii=False,
        ),
        end="",
    )
    return 0

def command_next(args: argparse.Namespace) -> int:
    return _run_agent_blind_next()


def command_validate(args: argparse.Namespace) -> int:
    try:
        alias, _source = validate_workflow_definition(args.alias)
    except WorkflowCommandError as error:
        print(
            json.dumps({"status": error.status, "reason": error.reason}, ensure_ascii=False),
            end="",
        )
        return 1
    except OSError:
        print(
            json.dumps(
                {"status": "invalid", "reason": "Workflow definition could not be read"},
                ensure_ascii=False,
            ),
            end="",
        )
        return 1
    print(json.dumps({"status": "valid", "alias": alias}, ensure_ascii=False), end="")
    return 0


def _print_task_result(result) -> int:
    payload = {
        "status": result.status,
        "task": result.task.payload,
    }
    if result.status in {"active", "blocked"}:
        payload["instruction"] = result.instruction
    if result.status == "blocked":
        payload["check"] = {"gate": result.gate, "reason": result.reason}
    print(json.dumps(payload, ensure_ascii=False), end="")
    return 1 if result.status == "blocked" else 0


def _run_human_command(decision: str, decision_payload: str, *, advance: bool = False) -> int:
    try:
        result = record_human_decision(None, decision, decision_payload, advance=advance)
    except WorkflowCommandError as error:
        _print_workflow_error(error)
        return 1
    except OSError:
        print(
            json.dumps(
                {"status": "error", "reason": "Workflow storage could not be read or written"}
            ),
            end="",
        )
        return 1
    return _print_task_result(result)


def command_approve(args: argparse.Namespace) -> int:
    return _run_human_command("approved", args.note, advance=args.next)


def command_reject(args: argparse.Namespace) -> int:
    return _run_human_command("rejected", args.reason)


def build_parser() -> argparse.ArgumentParser:
    parser = AgentWorkflowParser(prog="awh")
    subparsers = parser.add_subparsers(dest="command")
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("alias", help="Workflow catalog alias")
    start_parser.add_argument("--task", required=True, help="Stable task title")
    start_parser.add_argument(
        "--var",
        dest="variables",
        action="append",
        default=[],
        help="Repeatable start input name=value",
    )

    next_parser = subparsers.add_parser("next")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("alias", help="Workflow catalog alias")

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("--note", default="", help="Optional approval note")
    approve_parser.add_argument(
        "--next",
        action="store_true",
        help="Record approval and immediately attempt the next transition",
    )

    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("--reason", required=True, help="Required rejection reason")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "start":
        return command_start(args)
    if args.command == "next":
        return command_next(args)
    if args.command == "validate":
        return command_validate(args)
    if args.command == "approve":
        return command_approve(args)
    if args.command == "reject":
        return command_reject(args)

    print(
        json.dumps(
            {
                "status": "error",
                "reason": "A workflow command is required",
                "hint": "Run awh start <workflow-alias> --task <title> or awh next",
            }
        ),
        end="",
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
