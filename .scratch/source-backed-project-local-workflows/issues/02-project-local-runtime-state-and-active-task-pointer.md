# 02 — Project-local runtime state and active-task pointer

**What to build:** Runtime state moves into the target project and is organized as one lightweight active-task pointer plus one authoritative state file and one history file per task. The workflow runtime remains visible in the project, remains read-only to the agent, and remains uniquely written by the CLI.

**Blocked by:** 01 — Source-backed workflow package resolution.

**Status:** ready-for-agent

- [ ] A new workflow run stores its active-task pointer in the project's runtime-state directory.
- [ ] The active-task pointer contains only the pointer schema, task id, workflow alias, and normalized task title.
- [ ] An active task stores its runtime state in a task-scoped directory whose name keeps the existing stable task id format.
- [ ] The authoritative runtime state contains the agreed identity set, including current step, workflow identity, source package, and workflow-definition fingerprint.
- [ ] The runtime state is human-readable UTF-8 JSON and remains the sole authoritative current-state source.
- [ ] Each task has an append-only history log in its task-scoped runtime directory.
- [ ] A completed task removes the active pointer while retaining its task-scoped runtime directory.
- [ ] Black-box CLI tests verify start and next behavior using only project-local runtime state.
- [ ] Runtime files remain agent-readable but are not modified by any workflow command.
