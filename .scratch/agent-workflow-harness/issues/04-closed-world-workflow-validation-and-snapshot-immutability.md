# 04 — Closed-world workflow validation and snapshot immutability

**What to build:** invalid or ambiguous workflow definitions are rejected at initialization, and an already initialized task continues to use its copied workflow snapshot instead of the original source file.

**Blocked by:** 02 — Complete a workflow through repeated `next` calls

**Status:** ready-for-agent

- [ ] Initialization rejects a workflow with multiple outgoing transitions from one non-terminal step
- [ ] Initialization rejects a workflow with missing or unreachable steps
- [ ] Initialization rejects a workflow without a terminal step
- [ ] Initialization rejects a workflow without an inline guide for each step
- [ ] Reinitializing with a different workflow path is refused
- [ ] Updating the original workflow does not change an active task’s snapshot
- [ ] The task directory records the workflow snapshot’s provenance and hash
