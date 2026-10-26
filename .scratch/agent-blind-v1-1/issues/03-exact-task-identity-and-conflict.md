# 03 — Exact task identity and conflict handling

**What to build:** one project has one active task identity, and `start`/`next` can distinguish “resume the current task”, “conflict with a different task”, and “repair a stale or missing task anchor” without ever exposing internal control-plane identifiers.

**Blocked by:** 01 — Alias-driven start in a control-plane workspace, 02 — Agent-blind stage traversal

**Status:** ready-for-agent

- [ ] A repeated `start` with the same alias and normalized task title resumes the active task without advancing state
- [ ] `start` with a different alias or title returns `conflict` with the active task’s title
- [ ] The control plane never provides a path for an agent to switch the active task implicitly
- [ ] A missing or altered task anchor is rebuilt from the authoritative current-task record
- [ ] A repository task anchor without a matching active run returns `error`, not an implicit new-task start
- [ ] Task titles are trimmed, normalized, and exactly matched
