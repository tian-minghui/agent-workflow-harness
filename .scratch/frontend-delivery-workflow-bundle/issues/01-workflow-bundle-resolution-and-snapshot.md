# 01 — Workflow bundle resolution and snapshot

**What to build:** A workflow alias may point to a complete workflow bundle, not only a standalone YAML definition. Starting such an alias creates a task snapshot that preserves the full bundle, so later stages can use assets shipped with the workflow without depending on the agent’s current working directory.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Alias resolution supports a workflow bundle containing a workflow definition and its resource files
- [ ] The existing standalone-YAML workflow format keeps working without a breaking migration
- [ ] Starting a bundle-backed alias copies the whole bundle into the task snapshot, not only the YAML definition
- [ ] The workflow lock records the source and stability of the full bundle
- [ ] Start remains agent-blind and does not expose internal paths or snapshot locations in the response
- [ ] A start test from an unrelated project proves the bundle is usable from the first stage
- [ ] Test/test fixtures cover both legacy single-file aliases and directory-backed aliases

