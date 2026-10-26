# 09 — Cover repeated `next` on unchanged non-terminal work

**What to build:** when work has not changed and the current gate still fails, repeated `wf next` calls must be stable, non-advancing, and produce the same blocking reason.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] A non-terminal step with a missing or unchanged artifact does not advance across repeated calls
- [ ] Repeated failed calls return the same failed reason
- [ ] Repeated failed calls do not cause a state transition
- [ ] The task directory remains usable after repeated invocation
- [ ] The stale case is covered through the public CLI seam, not a helper function
