# 03 — Frontend-delivery workflow bundle adoption

**What to build:** Upgrade the frontend-delivery alias to a first-class directory workflow package combining a workflow definition, its reports, and the runtime resources they use. As a result, the workflow’s code-review stage works from any unrelated project directory without relying on an example checkout or a relative path that assumes the harness repository is present.

**Blocked by:** 01 — Workflow bundle resolution and snapshot, 02 — Resource-aware gate execution

**Status:** ready-for-agent

- [ ] The frontend-delivery alias resolves from a workflow bundle, not a bare standalone YAML definition
- [ ] Reports, templates, and runtime resources are colocated with the workflow definition
- [ ] The workflow can still complete its full stage sequence from an external project
- [ ] The code-review stage uses the bundled resource and template, not files under the project working directory
- [ ] The code-review gate preserves validation logic requiring all discovered issues to be marked as fixed
- [ ] The agent-visible instructions describe outcomes, not control-plane file paths
- [ ] The workflow remains a production definition rather than depending on the `examples/` directory as runtime infrastructure

