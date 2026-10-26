# 02 — Complete a workflow through repeated `next` calls

**What to build:** a workflow run can advance across multiple distinct `wf next` calls using only the task directory, reaching the terminal step and then remaining stably finished on later calls.

**Blocked by:** 01 — Minimal single-step traversal

**Status:** ready-for-agent

- [ ] Repeated `next` invocations do not require the workflow source path
- [ ] The task directory remains self-contained across calls
- [ ] The workflow can advance through more than one non-terminal step
- [ ] The terminal step returns `done: true`
- [ ] After completion, further calls produce a stable, non-destructive response
