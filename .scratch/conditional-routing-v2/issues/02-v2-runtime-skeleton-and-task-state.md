# 02 — V2 runtime skeleton and task state

**What to build:** evolve the control-plane runtime to start and advance one clean linear v2 workflow through the CLI while preserving the agent-blind response contract. This slice establishes task state v2 as the authoritative execution state and gives old v1 state a deterministic, operator-facing error.

**Blocked by:** 01 — Workflow v2 parser and inline validation.

**Status:** done

- [ ] A new v2 task is admitted from a minimal source-backed v2 workflow and stores task state version 2.
- [ ] The active-task pointer remains limited to the existing task identity fields.
- [ ] State v2 contains the authoritative current step, workflow source identity, immutable inputs map, fact map, visited-step set, and backedge counter map as empty maps where not yet used.
- [ ] `wf start` returns the initial work order without evaluating gates or progressing.
- [ ] `wf next` advances one non-terminal step after its ordinary gates pass and emits only the existing five-status execution response.
- [ ] A terminal v2 transition returns `done` and leaves the pointer removal and task-history behavior consistent with the runtime contract.
- [ ] An old v1 active task state surfaces as `error`, with a hint to inspect evidence and start a new v2 task, and is not auto-migrated.
- [ ] Existing black-box task interviews still exercise source drift, pointer/state integrity, and response stability at the CLI seam.
