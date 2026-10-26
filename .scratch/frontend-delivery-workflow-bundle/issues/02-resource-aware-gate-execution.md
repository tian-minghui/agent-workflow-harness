# 02 — Resource-aware gate execution

**What to build:** Workflow assets such as reports, templates, and runtime scripts can be referenced by a gate with unambiguous path semantics: project files resolve against the target project, while workflow-owned assets resolve against the task snapshot. A gate that depends on a bundled script must work from any project directory, including a project that does not contain the harness repository.

**Blocked by:** 01 — Workflow bundle resolution and snapshot

**Status:** ready-for-agent

- [ ] Gate steps can reference workflow-owned resources without executing commands against the project’s working directory as if it were the workflow source
- [ ] Resource paths and project paths are distinguished explicitly, so bundled scripts and templates cannot be confused with project files
- [ ] Resource-backed gate execution supports Python scripts shipped with the workflow bundle and passes clean, explicit result text back to the harness
- [ ] A passing resource-backed gate and a failing resource-backed gate both work from an unrelated project directory
- [ ] The end-to-end demonstration starts on one stage, triggers the resource-backed gate, and shows the gate’s success or explicit failure response
- [ ] Existing command and file gates continue to use project-relative paths
- [ ] The gate implementation preserves the agent-blind response contract rather than replacing it with raw runtime output

