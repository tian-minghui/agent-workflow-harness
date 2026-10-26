# Task artifact directory is separate from runtime state

A running task gets a project-local artifact directory for workflow business artifacts, while the runtime task directory remains dedicated to authoritative state and history. The artifact directory is written as project artifacts by the agent and is referenced by workflow guidance and gates; it does not replace or contaminate `.workflow-harness/tasks/<task-id>/`.

The task artifact directory path is `<project>/.workflow-harness/task-artifacts/<task-slug>-<task-id>/`. The task slug is derived deterministically from the accepted task title and suffixed with the full task ID, not supplied as a separate task directory name. The title itself remains human-readable, while the slug is safe for filesystem use across the supported platforms.

`${taskDir}` resolves to the project-relative artifact-directory path, not an absolute machine path. This preserves the existing project-relative semantics of file gates, workflow-script arguments, and human evidence paths. It differs intentionally from `${workflowDir}`, which may point outside the project and therefore resolves to its absolute source-package directory.

A task title must therefore be English: a single line of 5–120 characters containing only ASCII letters, digits, spaces, and hyphens. The title is still normalized by trimming and collapsing whitespace, and task resume still uses exact title matching. The title must be a natural English task title rather than a forced directory-name format such as `implement-user-profile-export`.

The slug is lowercase, retains ASCII letters and digits, folds spaces and consecutive hyphens to a single hyphen, trims leading and trailing hyphens, and is truncated to 64 characters. The artifact-directory name appends the complete task ID after a hyphen, so identical or similarly truncated titles can never reuse one artifact directory. The resulting directory name remains readable because the title prefix carries the semantics, and remains bounded under common filesystem limits; uniqueness does not rely on a probabilistic eight-character ID suffix.

The control plane creates the task artifact directory when it creates a new task, before returning the first work order. Resuming the same task never clears or replaces the directory. Reaching the terminal step removes the active-task pointer but does not delete either the runtime task directory or the task artifact directory; artifacts remain available as durable evidence and may be moved or committed according to the target project’s policy.

When `wf start` creates a new task, the control plane computes the project-relative artifact path once and stores it in authoritative task state. Subsequent template resolution reads that stored `artifact_dir` fact; it does not re-derive the path from the title during the task lifetime. If state lacks the field or its value does not identify the retained task artifact directory, the control plane returns an integrity error rather than repairing or relocating artifacts.

The lightweight `task.json` anchor does not duplicate `artifact_dir`. The anchor continues to identify the active task only, while authoritative task state remains the sole source for the artifact path used by `${taskDir}`.

The harness does not prescribe or edit the target project’s ignore rules. Whether completed task artifacts are committed, copied into a delivery location, or remain local is a project-level decision. This keeps workflow business artifacts under normal project ownership instead of having the control plane impose a version-control policy.

Workflow authoring guidance requires model-produced business artifacts, such as requirements, specs, reports, and review notes, to use concrete paths under the current `${taskDir}`. Implementation results that belong to the target project, including source code, tests, and configuration, remain in their normal project locations. The harness documents this as an authoring rule and does not force every file gate or human-evidence path to live under `${taskDir}`, because evidence may legitimately include project files.
