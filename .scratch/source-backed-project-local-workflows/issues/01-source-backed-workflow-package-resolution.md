# 01 — Source-backed workflow package resolution

**What to build:** A workflow alias resolves to a source-backed workflow package stored in a project root, a user fallback root, or a built-in fallback root. The resolved package is used directly, not copied, and start returns the current stage work order while binding the workflow to one source package.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Workflow aliases resolve in fixed order: project root, user root, then built-in root.
- [ ] Each workflow package is a directory named after its alias and contains the required workflow definition file.
- [ ] The standalone workflow-file form is not used for project or user packages.
- [ ] Built-in workflows are organized in the same source-backed package layout as project and user workflows.
- [ ] A start command resolves the alias once, returns the current stage work order, and does not copy the workflow package.
- [ ] The resolved absolute source directory and workflow-definition fingerprint are stored with the active task state.
- [ ] Starting from any project subdirectory resolves the same project workflow root.
- [ ] Tests show project overrides user, user overrides built-in, and start remains usable through the existing CLI response contract.
