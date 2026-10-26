# 05 — History as authoritative state source

**What to build:** the task’s derived state can be rebuilt from the append-only history log, proving that history is the authoritative source and state is only a projection.

**Blocked by:** 02 — Complete a workflow through repeated `next` calls, 03 — Ordered multi-gate fail-fast output

**Status:** ready-for-agent

- [ ] History is append-only
- [ ] Each successful transition is recorded with step and target
- [ ] Each failed attempt is recorded with step, gate, and reason
- [ ] State can be reconstructed from history
- [ ] Removing the state projection does not prevent recovery
- [ ] Rebuilding state produces the same observable current step
- [ ] No external evidence or rich command logs are required
