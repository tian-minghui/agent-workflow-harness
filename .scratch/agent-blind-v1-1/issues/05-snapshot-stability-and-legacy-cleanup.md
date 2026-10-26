# 05 — Snapshot stability and legacy cleanup

**What to build:** an active control-plane run remains bound to its own workflow snapshot, while the v1 `--workflow` and `--task-dir` interface is removed cleanly so the only public surface is the agent-blind v1.1 protocol.

**Blocked by:** 02 — Agent-blind stage traversal

**Status:** ready-for-agent

- [ ] Editing the source workflow definition does not change the active run
- [ ] The control-plane snapshot is used for stage, gate, and guide resolution
- [ ] The v1 `--workflow` argument is rejected
- [ ] The v1 `--task-dir` argument is rejected
- [ ] Existing v1 task directories are historical records, not runnable state
- [ ] No public test, command, or response can reintroduce a workflow path or task directory
- [ ] The v1.1 interface still passes all rewritten black-box CLI tests
