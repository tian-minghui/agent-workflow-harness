# 01 — Alias-driven start in a control-plane workspace

**What to build:** the first complete v1.1 path where a project can start a workflow by alias, without any workflow or task-directory arguments, and receive an active work order while authoritative run data is placed into the control-plane home.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `wf start <workflow-alias> --task <title>` resolves a workflow alias through the built-in catalog
- [ ] A user-installed alias overrides the built-in alias of the same name
- [ ] An invalid alias returns a stable `error` response with a safe next-action hint
- [ ] The active task is created under the control-plane home, not in the project repository
- [ ] The project-level current-task pointer and the repository task anchor are created
- [ ] The start response is `active` with the first stage instruction and task title
- [ ] No response exposes a workflow path, task ID, or stage identity
