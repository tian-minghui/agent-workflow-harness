# 06 — Meaningful history outcomes

**What to build:** Each task records a concise, append-only history of the outcomes that materially affect the run, while runtime state remains authoritative. The history log supports audit and diagnosis but is not used to rebuild current state.

**Blocked by:** 02 — Project-local runtime state and active-task pointer; 04 — Single-task admission and pointer/state integrity; 05 — Workflow-definition source-drift policy.

**Status:** ready-for-agent

- [ ] Start records the task's initial created state.
- [ ] Successful stage transitions record the transition that produced the new current state.
- [ ] Failed automatic gates leave a meaningful blocked record.
- [ ] Unexpected operational and integrity failures leave a meaningful error record.
- [ ] Human decisions are recorded in the active task's history.
- [ ] Workflow-definition source drift is recorded when detected.
- [ ] Completed tasks record terminal completion.
- [ ] Repeated ordinary parsing errors are not logged merely to inflate the file.
- [ ] Runtime state remains authoritative and is never rebuilt from the history log.
- [ ] Tests inspect only externally observable output and confirm the history remains append-only while state remains authoritative.
