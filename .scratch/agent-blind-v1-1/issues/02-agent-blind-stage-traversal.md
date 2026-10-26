# 02 — Agent-blind stage traversal

**What to build:** the first complete progression path through a v1.1 workflow where `wf next` evaluates the active stage, advances at most one transition, and returns an `active`, `blocked`, or `done` work order without exposing the state graph.

**Blocked by:** 01 — Alias-driven start in a control-plane workspace

**Status:** ready-for-agent

- [ ] `wf next` requires no path, workflow, or task arguments
- [ ] A passing current-stage gate advances exactly one transition
- [ ] A newly entered stage returns an `active` response with that stage’s instruction and the active task title
- [ ] A failing current-stage gate returns a `blocked` response with the current instruction and `check.gate`
- [ ] A terminal transition returns `done`
- [ ] `done` deletes the repository task anchor
- [ ] Control-plane history records successful transitions, blocked attempts, and completion
