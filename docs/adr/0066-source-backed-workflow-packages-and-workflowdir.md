# Source-backed workflow packages and `${workflowDir}`

A workflow alias resolves to a source-backed package, not to a task-local copy. Lookup starts in `<project>/.agents/workflows`, then falls back to `~/.agents/workflows`, then to the built-in catalog shipped with the harness. The same-alias override order remains project → user → built-in. The active stage guide remains free-form prose; when returned to the model, the harness replaces `${workflowDir}` with the resolved source package directory, for example `${workflowDir}/references/conventions.md`. The harness does not copy the package, compute an asset closure, or resolve nested references; the agent may read package assets directly, and future visibility policy is deferred to an explicit hook.

`wf start` resolves the alias once and stores the resulting source package path in the active task. `wf next` reuses that recorded path; it does not re-resolve the project, user, or built-in catalogs during an active run.

At `wf start`, the harness records a SHA-256 fingerprint of the source `workflow.yaml`. Each `wf next` rereads that source file and compares the fingerprint before evaluating the active step. If the file changed during the run, `wf next` returns an `error` response instead of advancing with a mutated graph or treating source drift as an agent-repairable gate. Reference, script, template, and asset files may change during the run; they are not versioned or closure-checked, because stage guidance and gate execution remain directly source-backed.

The `${workflowDir}` substitution is available consistently in model-facing prose (`guide` and human-gate requests) and executable `command` strings. Keeping one path variable across instruction and commands avoids forcing workflows to maintain separate relative-path conventions for references, scripts, assets, and tools.

Project, user, and built-in workflow roots are flat alias namespaces. A workflow package must be a directory named `<alias>` containing `workflow.yaml`; no extra domain or category layer is required, and the workflow alias is the directory name. This keeps `.agents/workflows` aligned with the one-directory-per-skill mental model and avoids manifest-style index maintenance.

A workflow package should recommend the skill-like layout below, but the harness treats it as guidance rather than mandatory validation:

```text
<alias>/
  workflow.yaml
  references/
  scripts/
  assets/
```

Only `workflow.yaml` is a core contract. Users may organize references, scripts, assets, templates, and other package files however they need, because the harness only supplies `${workflowDir}` and does not inspect their layout.

The substituted `${workflowDir}` value is the resolved, absolute source package directory, not the project-relative package path. Both model-facing prose and `command` strings then resolve consistently regardless of the caller's working directory.

The previous `~/.workflow-harness/workflows` catalog is not retained as a fallback. Workflow source packages are discovered in the project `.agents/workflows` root, the user `~/.agents/workflows` root, and the harness's built-in catalog. Runtime state is project-local and no longer uses `WF_HOME` (see ADR 0067).

`wf start` writes the resolved absolute source package path and the `workflow.yaml` SHA-256 fingerprint into the active task's `state.json`. The lightweight `task.json` pointer remains limited to `schema`, `task_id`, `workflow_alias`, and `title` so it does not become a second runtime state file.

A `wf start` request that matches the active alias and exact task title also follows the source-drift policy: it compares the active task's recorded `workflow.yaml` fingerprint before returning the resumed work order. If the source definition changed during the run, the command returns `error` rather than silently rebinding the active task to a changed workflow.

The response objects remain minimal and do not add a separate `workflow_dir` field. `${workflowDir}` is a substitution token for model-facing prose and executable command strings, not another response protocol field.
