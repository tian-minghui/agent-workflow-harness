# 10b — Workflow creator skill

**What to build:** add the manual-only `workflow-harness-creator` skill that uses the authoring guide and `wf validate` to create a source-backed v2 workflow package. It should be explicit-invocation-only, default to a project-local package, and protect existing packages from intentional-overwrite risk.

**Blocked by:** 10 — Workflow schema authoring guide.

**Status:** done

- [ ] The creator is manual-only and cannot auto-trigger from task-progress language.
- [ ] The creator defaults to creating a project-local workflow package.
- [ ] A new project-local package can be created directly after the user explicitly invokes the creator.
- [ ] The creator lists the alias, destination, and generated or modified files before touching an existing package and waits for approval.
- [ ] A user-level package is created only when explicitly requested for cross-project reuse.
- [ ] The creator rejects requests to modify a built-in workflow package.
- [ ] The creator produces a valid v2 package containing guide, gates, fact producers, and step-local transitions according to the schema guide.
- [ ] The creator invokes `wf validate` and refuses to mark a package finished while validation reports `invalid`.
- [ ] The creator does not modify an active task’s runtime files or the active task pointer.
- [ ] The skill knows no stage order and does not duplicate business workflow rules from the runner skill.
- [ ] Contract tests enforce manual-only wording, project-local default, existing-package confirmation, built-in write rejection, and dependency on the schema guide.
