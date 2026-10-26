# 04 — Single-task admission and pointer/state integrity

**What to build:** A project has one active workflow task at a time, and the current pointer, runtime state, and task directory must agree exactly. Existing start/admission semantics stay unchanged; any pointer/state mismatch or missing active task is treated as an operational error, not something the runner is allowed to repair or auto-start.

**Blocked by:** 02 — Project-local runtime state and active-task pointer.

**Status:** ready-for-agent

- [ ] A start with the exact active alias and normalized task title resumes the same active task.
- [ ] A start with a different workflow alias or task title returns `conflict`.
- [ ] A `wf next` with no active-task pointer returns `error` and does not create a new task.
- [ ] A task pointer pointing to a nonexistent task directory returns `error`.
- [ ] A missing, malformed, or mismatched pointer/state pair returns `error`.
- [ ] Runtime state is never reconstructed from history or silently repaired by the harness.
- [ ] A task reaching terminal completion removes the active pointer while retaining the task-scoped runtime directory.
- [ ] The project does not gain a second active task or a task-selection command.
- [ ] Tests cover resume, conflict, no-active-task, missing files, stale pointer, and completion behavior through the process-level CLI seam.
