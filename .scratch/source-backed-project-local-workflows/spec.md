Status: ready-for-agent

# Source-backed, project-local workflow runtime

## Problem Statement

Workflow authors cannot maintain reusable workflows the same way they maintain skills. Workflow assets live either in a framework-owned bundle or in a control-plane home, which detach them from the project that actually runs them. Agents therefore need a translation layer between “workflow definition,” “reference material,” and “runtime state,” and the harness spends effort making a copied snapshot behave like a source package.

The user wants workflows to feel like ordinary, project-maintained skill packages while the CLI retains the authority to decide progression. The current design also stores runtime state in a user-level control-plane home, which makes it harder to reason about a project’s active task and hides the most useful operational information from the person using the project.

## Solution

Workflow sources become source-backed, skill-like packages stored in known project, user, and built-in roots. The harness resolves an alias to one concrete package directory, binds that source to a run at start time, and never copies the package. The active guide and command strings may use a `${workflowDir}` path token, which the harness replaces with the package’s absolute source directory. The author is free to organize and reference package files like ordinary skill assets.

Runtime state becomes project-local and task-scoped. A project has one lightweight active-task pointer and one authoritative runtime state file per task. A task’s audit log is append-only and records meaningful workflow outcomes, but it is not a recovery source for state. The CLI remains the sole writer of runtime-state files; agents may read them but never modify them.

This separates three responsibilities clearly:
- workflow ownership,
- model-facing guidance,
- runtime progression.

## User Stories

1. As a workflow author, I want workflow sources stored in a standard project root, so that I can maintain them alongside my project’s other skill-like assets.
2. As a workflow author, I want a user-level root as a fallback, so that I can share workflows across projects without duplicating them into every repository.
3. As a workflow author, I want the harness to retain built-in workflows as a final fallback, so that standard flows remain usable without installation.
4. As a workflow author, I want the same alias to resolve by fixed precedence, so that a project workflow can deliberately override a user workflow.
5. As a workflow author, I want package lookup to be flat and simple, so that I do not need a manifest or nested category layer to publish a workflow.
6. As a workflow author, I want only the package’s `workflow.yaml` to be a hard contract, so that I am free to organize references, scripts, assets, and templates as my project requires.
7. As a workflow author, I want a recommended skill-like layout, so that workflow packages feel familiar even when the harness does not enforce every subdirectory.
8. As a workflow author, I want `${workflowDir}` to refer to the resolved source package, so that my guide and gate commands can point to assets without hardcoding machine-specific paths.
9. As a workflow author, I want `${workflowDir}` substituted at runtime, so that agents and commands receive a concrete absolute path.
10. As a workflow author, I want the harness not to parse or resolve nested references, so that my guidance remains a natural document like a skill’s guidance rather than a compiled bundle.
11. As a workflow author, I want source packages read directly rather than copied, so that package size and update cost do not grow with bundle complexity.
12. As a workflow author, I want the binding recorded once at start, so that the active run cannot silently switch between project, user, and built-in versions.
13. As a workflow author, I want only the active `workflow.yaml` fingerprinted, so that reference and script edits do not artificially invalidate an ongoing task.
14. As a workflow author, I want source drift to be an operational error, so that a running task cannot continue against a changed graph.
15. As a workflow author, I want `${workflowDir}` available in both prose and command strings, so that the same path variable works for guidance and automated checks.
16. As a workflow author, I want `${workflowDir}` available in human-review requests, so that reviewer-facing instructions can reference evidence in the same source package.
17. As a workflow author, I want the dedicated workflow-script gate retained, so that package scripts do not have to degrade into plain shell commands.
18. As a workflow author, I want a simple one-directory-per-workflow model, so that publishing and overriding workflows remain predictable.
19. As a workflow author, I want the workflow source to feel like a skill directory, so that I do not have to maintain a second authoring mental model.
20. As a coding agent, I want only the current stage work order returned, so that I do not have to infer future stages from the guide.
21. As a coding agent, I want the response contract to stay minimal and unchanged, so that runtime changes do not make the workflow protocol harder to use.
22. As a coding agent, I want `${workflowDir}` replaced inside the instruction text, so that I can follow package references without a second path-handling step.
23. As a coding agent, I want package assets readable directly, so that I can follow guidance the same way I follow a skill’s supporting documents.
24. As a coding agent, I want the workflow harness not to synthesize my instructions, so that I can see the author’s actual wording.
25. As a coding agent, I want project runtime files readable, so that I can inspect the active task and workflow path when needed.
26. As a coding agent, I want runtime files to be read-only, so that I cannot accidentally corrupt the authoritative state.
27. As a coding agent, I want a single active-task pointer, so that I always know which run I am continuing.
28. As a coding agent, I want no automatic start on `wf next`, so that a missing active task remains a clear error rather than a silent new task.
29. As a coding agent, I want existing start/resume/conflict semantics preserved, so that the current command protocol does not drift into new task-selection rules.
30. As an operator, I want runtime state inside the project, so that a project’s active workflow is colocated with its artifacts.
31. As an operator, I want task state stored at task granularity, so that completed runs remain inspectable after the active pointer is removed.
32. As an operator, I want the active pointer removed on done, so that a project’s current-task state remains unambiguous.
33. As an operator, I want task records preserved after completion, so that I can audit a finished workflow without freezing the project.
34. As an operator, I want the runtime state to be human-readable JSON, so that I can debug a task without parsing a compressed internal format.
35. As an operator, I want the audit log to record meaningful outcomes, so that I can see the run’s progression, blockers, approvals, and errors.
36. As an operator, I want the history log not used as a recovery source, so that runtime correctness depends on one authoritative state file.
37. As an operator, I want invalid or inconsistent state reported as an error, so that an agent cannot “repair” a bad pointer by guessing.
38. As an operator, I want no `wf status` command, so that the CLI surface remains small and the visible state files are the status interface.
39. As an operator, I want legacy control-plane state not auto-migrated, so that the new behavior is a clean break rather than a silent source of runtime ambiguity.
40. As a maintainer, I want existing black-box CLI tests reused, so that this redesign is verified through the same stable seam rather than through implementation-specific details.
41. As a maintainer, I want workflow source lookup and runtime-state rules testable in isolation, so that changes in workflow authoring do not silently change task progression.
42. As a maintainer, I want the response schema stable, so that external consumers and runner skills do not need to learn a new protocol.

## Implementation Decisions

- Workflow sources are resolved from three fixed roots:
  1. the project workflow root,
  2. the user workflow root,
  3. the harness’s built-in workflow root.
- Alias resolution uses the order project, user, then built-in.
- The source package is a directory named after the alias.
- Only `workflow.yaml` is required; supporting directories are a recommendation, not a hard contract.
- No manifest or centralized index is introduced.
- A workflow alias is resolved once when a task starts.
- The resolved source package path is stored with the task state.
- `wf next` reuses the recorded source path and does not re-run alias resolution.
- The source `workflow.yaml` is fingerprinted at start.
- The current `workflow.yaml` is re-read and fingerprinted before `wf next` advances a task.
- If the fingerprint changes during the run, the result is an operational `error`, not a business `blocked` state.
- `wf start` with the same active alias and exact title also checks the fingerprint before resuming.
- Only the workflow definition file is subject to this drift check; references, scripts, templates, and assets may change during the run.
- `${workflowDir}` is a path token available in:
  - `guide`,
  - `human.request`,
  - `command` strings.
- `${workflowDir}` is replaced with an absolute source-package path.
- The response object keeps the existing minimal schema and does not expose a separate workflow-directory field.
- The harness does not parse or transform guidance beyond `${workflowDir}` substitution.
- The harness does not resolve nested references or validate their reachability.
- The harness does not copy the workflow package.
- The dedicated workflow-script gate remains, rather than collapsing package verification into plain command strings.
- Workflow stage guidance remains free-form and is projected verbatim to the current run.
- Runtime state moves into the project’s workflow runtime directory.
- The project runtime directory keeps:
  - one lightweight active-task pointer,
  - one per-task directory for authoritative state and history.
- The active-task pointer contains only the pointer schema, task id, workflow alias, and title.
- The per-task runtime state contains a minimal closed identity set:
  - state schema,
  - task id,
  - workflow alias,
  - task title,
  - current step,
  - absolute workflow source directory,
  - workflow definition fingerprint.
- The per-task runtime state is authoritative.
- The per-task history log is append-only and records meaningful outcomes such as start, advance, block, error, completion, source drift, and human decision.
- The history log is not used to reconstruct or repair runtime state.
- The runtime state uses readable UTF-8 JSON.
- Runtime state writes are atomic.
- Agent-facing runtime files are visible but treated as read-only.
- The CLI is the only writer of runtime files.
- The project uses one active task at a time.
- The active-task pointer is removed when a task reaches done.
- Completed task directories are preserved for inspection.
- `wf next` never auto-starts a missing task.
- Existing start/resume/conflict semantics are preserved:
  - same alias and exact title → resume,
  - different active alias or title → conflict,
  - no active task → create a new task.
- Task-dir names remain the existing stable task-id style, with no timestamp or title-derived format.
- No automatic migration from the former user-level control-plane directory is performed.
- The old user-level workflow catalog is not retained as a fallback.
- No `wf status` command is added.
- No new structured response field is added for workflow path or task status.

## Testing Decisions

- The primary testing seam remains the process-level CLI boundary.
- Tests should invoke `wf start`, `wf next`, `wf approve`, and `wf reject` through subprocesses and assert only externally observable behavior.
- Tests should use temporary projects and isolated project roots so they never read or mutate a real user’s workflow sources.
- The suite should continue to assert the stable five-status response schema.
- Source-lookup tests should confirm:
  - project workflows override user workflows,
  - user workflows override built-in workflows,
  - a directory package named after the alias is used,
  - a source package is resolved once and bound to the active task.
- Guide and command tests should confirm:
  - `${workflowDir}` is replaced with an absolute path in guide text,
  - the same replacement works in human review requests,
  - workflow command strings resolve package paths correctly,
  - the response does not expose a separate workflow-directory field.
- Source-drift tests should confirm:
  - `wf next` refuses to advance when `workflow.yaml` changes during the run,
  - a matching `wf start` resume also refuses to proceed when the fingerprint changed,
  - changing only a reference or script file does not invalidate the task’s stored graph binding.
- Runtime-state tests should confirm:
  - the active-task pointer is created at start,
  - the pointer contains only the four agreed fields,
  - the per-task state file is human-readable and contains the agreed identity set,
  - the pinned source package and graph fingerprint are persisted,
  - state remains authoritative and is not rebuilt from history.
- Pointer-integrity tests should confirm:
  - a missing pointer or state file returns an error,
  - a task pointer that points to a nonexistent task directory returns an error,
  - pointer and state identity mismatches return an error,
  - the harness does not automatically repair either side.
- Lifecycle tests should confirm:
  - the active pointer is removed after done,
  - the completed task directory remains available,
  - task admission and conflict semantics are unchanged,
  - `wf next` does not auto-start a missing task.
- History tests should confirm:
  - start and transition events are recorded,
  - blocked and error outcomes are recorded,
  - human decisions are recorded,
  - source-drift events are recorded,
  - changing history cannot change runtime state.
- Workflow-script gate tests should confirm:
  - the dedicated gate still resolves its script against the package directory,
  - its project arguments still resolve against the target project root,
  - gate failures remain `blocked` rather than `error`.
- Read-only behavior tests should confirm:
  - runtime files are readable,
  - the CLI writes them during start and next,
  - direct editing is not required or expected by any workflow.

## Out of Scope

- A manifest or centralized workflow index.
- Nested workflow categories or domain/category catalog layers.
- Automatic migration from the old user-level control-plane home.
- Reading user-level workflow sources as a legacy fallback.
- A new status, history, or task-selection command.
- A new structured model-facing response field.
- Multiple concurrent active tasks.
- Automatic task switching or a task selector.
- Recompiling or caching workflow packages.
- Parsing, validating, or resolving model-authored reference chains.
- Checking whether referenced package files exist.
- Workflow authoring UI or a dedicated editor.
- A host sandbox or server control plane.
- A trusted reviewer identity service.
- Semantic validation of guide contents.
- Adding new workflow business steps.
- Modifying the `prd-to-spec` workflow itself.

## Further Notes

- The design intentionally moves toward a source-backed, skill-like package model rather than a copied control-plane asset.
- The design intentionally moves toward project-local runtime state rather than a hidden user-level state area.
- Assets are readable because the harness’s authority comes from runtime state and command progression, not from hiding files.
- The only required runtime dependencies are the source package’s `workflow.yaml` and the project-local runtime state.
- A later host sandbox, read hook, or permission boundary can tighten visibility without changing the package layout.
- The intended workflow authoring experience remains: edit source files, start a task, follow the current work order, and let the control plane decide progression.
