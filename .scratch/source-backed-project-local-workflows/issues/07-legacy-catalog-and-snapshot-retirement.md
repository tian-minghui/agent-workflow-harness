# 07 — Legacy catalog and snapshot retirement

**What to build:** After the source-backed project-local workflow runtime is in place, the old user-level workflow catalog and task snapshot behavior are removed. The new resolution and runtime remain the only supported model, without an automatic migration path from the old control-plane layout.

**Blocked by:** 01 — Source-backed workflow package resolution; 02 — Project-local runtime state and active-task pointer; 03 — `${workflowDir}` substitution across guide and gates; 04 — Single-task admission and pointer/state integrity; 05 — Workflow-definition source-drift policy; 06 — Meaningful history outcomes.

**Status:** ready-for-agent

- [ ] The old user-level workflow catalog is no longer read during alias resolution.
- [ ] The old user-level control-plane storage is no longer used as a runtime fallback.
- [ ] The workflow runtime no longer creates or reads workflow snapshots or copied workflow packages.
- [ ] No workflow source is copied into the runtime state directory.
- [ ] Built-in workflows are fully source-backed and no longer depend on snapshot-specific read paths.
- [ ] No automatic migration reads or transforms old user-level workflow or task data.
- [ ] The five-status CLI response contract remains unchanged.
- [ ] Existing workflow-script and human-gate behavior remains compatible with the source-backed layout.
- [ ] Black-box tests confirm start, next, approve, reject, and done behavior without depending on any legacy path.
- [ ] A clean isolated project proves the new resolution and runtime paths are sufficient.
