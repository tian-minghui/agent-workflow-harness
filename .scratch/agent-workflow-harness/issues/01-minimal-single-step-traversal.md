# 01 — Minimal single-step traversal

**What to build:** the first complete, runnable path through the workflow engine: a task directory is initialized from a workflow file, the current step runs one gate, the CLI advances to the next step, returns the next step’s guide, and writes one append-only history event.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] A fresh task directory can be created from a minimal workflow
- [ ] The workflow snapshot is copied into the task directory
- [ ] The first step’s inline guide is returned in the success JSON object
- [ ] The first step’s single gate is executed
- [ ] A successful gate advances the workflow to the next step
- [ ] One history event records the successful transition
