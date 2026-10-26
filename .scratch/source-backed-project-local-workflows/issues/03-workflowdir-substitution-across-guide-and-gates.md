# 03 — `${workflowDir}` substitution across guide and gates

**What to build:** Workflow guidance, human-review requests, and command gates can use one `${workflowDir}` token, which the harness replaces with the resolved absolute workflow source directory. The instruction text remains otherwise unchanged, and the response schema does not gain a workflow-path field.

**Blocked by:** 01 — Source-backed workflow package resolution; 02 — Project-local runtime state and active-task pointer.

**Status:** ready-for-agent

- [ ] `${workflowDir}` is replaced with an absolute source directory in returned guide text.
- [ ] The same token works in workflow command strings.
- [ ] The same token works in human-gate request text.
- [ ] The response objects remain minimal and do not add a separate workflow-directory or path field.
- [ ] The dedicated workflow-script gate still resolves scripts against the source package directory.
- [ ] Command-gate working directories continue to resolve project-relative operands against the target project.
- [ ] Guidance is returned verbatim except for `${workflowDir}` substitution.
- [ ] Reference and asset files may be referenced by the author, but the harness does not resolve, validate, inline, or copy them.
- [ ] Tests cover guide text, command execution, human-gate request text, and the unchanged response schema.
