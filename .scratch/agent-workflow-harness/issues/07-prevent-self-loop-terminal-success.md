# 07 — Prevent non-terminal self-loop terminal success

**What to build:** a self-loop must not be mistaken for reaching the workflow’s terminal completion state. Workflow completion must remain tied to the explicit terminal step, not to a missing outgoing transition.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] A workflow with a non-terminal self-loop is rejected during validation
- [ ] The workflow validator reports self-loops as invalid topology
- [ ] A valid terminal step still produces `done: true`
- [ ] A non-terminal step does not produce `done: true`
- [ ] The transition lookup no longer treats silence as completion
