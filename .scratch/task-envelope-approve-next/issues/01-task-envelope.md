# 01 — Task envelope on command responses

**What to build:** A user can call any task-facing command and receive a stable enriched `task` object containing:

- `id`
- `title`
- `step`
- `artifactDir`

without reading runtime files or deriving context from a gate error. This applies to:

- `wf start`
- `wf next`
- `wf approve`
- `wf reject`

The existing statuses and fields must remain unchanged.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] `wf start` returns `task.id`, `task.title`, `task.step`, and `task.artifactDir`
- [ ] `wf next` returns the same four fields
- [ ] `wf approve` returns the same four fields
- [ ] `wf reject` returns the same four fields
- [ ] Existing `status`, `instruction`, and `check` fields remain compatible
- [ ] The five-status contract remains `active / blocked / done / conflict / error`
- [ ] No new status or response schema is introduced
- [ ] Existing command behavior is unchanged; only response data is enriched
- [ ] Black-box tests exercise each affected command through the CLI boundary
- [ ] No artifact, gate, or route semantics change
