# 09 — Runner skill v2 contract

**What to build:** update the thin runner skill so an invited coding agent can continue using the existing start/next/decision protocol on a v2 task, without learning business graph rules or route semantics. The released skill should remain protocol-thin, sequence-agnostic, and manual-adjacent to the workflow.

**Blocked by:** 07 — V2 built-in migration and clean v1 retirement.

**Status:** done

- [ ] The runner skill documents `wf start` with repeatable `--var` inputs.
- [ ] The runner skill continues to explain only the five task-execution statuses.
- [ ] `approve` and `reject` remain record-only, with none of them advancing the stage or route.
- [ ] Route evaluation failures are understood as `error` responses, never as current-stage `blocked` instructions.
- [ ] The runner skill does not document candidate edges, future stages, graph structure, gates, or business deliverables.
- [ ] The skill repeats an active task title exactly and does not silently replace an active task with a new start input vector.
- [ ] The skill keeps the existing hard boundaries on not self-declaring progress and not editing runtime state.
- [ ] Contract tests verify that forbidden legacy arguments and forbidden graph knowledge have not reappeared.
