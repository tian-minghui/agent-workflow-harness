# 06 — Skill and example integration

**What to build:** a user-facing workflow skill can preflight the active task, generate or reuse a stable task title, and drive the v1.1 agent-blind protocol end to end, culminating in a complete documented workflow run with no workflow YAML exposed.

**Blocked by:** 01 — Alias-driven start in a control-plane workspace, 02 — Agent-blind stage traversal, 03 — Exact task identity and conflict handling, 04 — Project-rooted command gates and bounded repair output, 05 — Snapshot stability and legacy cleanup

**Status:** ready-for-agent

- [ ] The skill preflight reads the repository task anchor and decides between `start` and `next`
- [ ] A new generated task title is one line and 5–120 characters
- [ ] An active task title is reused exactly, not edited by the skill
- [ ] `start` and `next` responses are interpreted using the five-status contract
- [ ] `blocked` responses repair the same stage, never the next one
- [ ] `done` responses stop further workflow work
- [ ] The skill does not read workflow YAML or edit the task anchor
- [ ] An end-to-end example workflow run completes through the new protocol
