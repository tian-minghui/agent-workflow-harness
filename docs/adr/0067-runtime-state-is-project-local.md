# Runtime state is project-local

Workflow runtime state belongs to the target project, not to a user-level control-plane home. The project's `.workflow-harness/` directory holds the authoritative state and audit log, including `state.json` and `history.jsonl`; these files are visible to the agent because visibility is no longer relied on as a control-plane boundary. `state.json` is authoritative for the active stage, bound source package, and related execution variables; `history.jsonl` remains an append-only operational log. All runtime information that was previously placed under a user-level process directory moves into the project directory. This supersedes the local, user-controlled control-plane-home model while keeping the state machine authoritative.

Version-control policy for `.workflow-harness/` is left to the project itself. The harness does not require `state.json` or `history.jsonl` to be committed; the recommended default is to ignore runtime state, but a project may intentionally commit it when it wants an audit trail in the repository.

Runtime records remain task-scoped inside the project, while the project maintains one lightweight current-task pointer:

```text
<project>/.workflow-harness/
  task.json
  task-artifacts/
  tasks/
    <task-id>/
      state.json
      history.jsonl
```

`task.json` is the CLI-maintained active-task pointer; the per-task directory is the runtime instance. The pointer exists so runner skills can cheaply check which task is active without reading a full `state.json`. `task-artifacts/` is the separate task-scoped business-artifact directory; it is not a control-plane state-instance directory.

When a task reaches `done`, the harness removes `task.json` so the project has no active-task pointer, while retaining `tasks/<task-id>/` with its `state.json` and `history.jsonl` for audit and later inspection. Deleting the pointer represents completion; the task record remains available as a fact source or historical entity.

A project has one active workflow task at a time. `task.json` points to that single active task, and `wf next` always advances that task. More general multi-task selection and explicit task switching are deliberately deferred; the pointer shape may later be extended without changing the active-only behavior. Completed task records remain under `tasks/` for inspection.

The earlier single-task admission rule is preserved: `wf start` resumes an existing run only when the requested workflow alias and normalized task title exactly match the active task, and it returns `conflict` for a different active task. Moving runtime state into the project changes storage location, not task admission or progression semantics.

The `task.json` schema is a minimal active-task pointer containing four fields: `schema`, `task_id`, `workflow_alias`, and `title`. This is enough to locate `tasks/<task-id>/` and to let a runner skill perform cheap exact-match preflight, without exposing the full state machine, history, or future stages.

If `task.json` and `state.json` disagree, are missing, or point to a nonexistent task directory, `wf next` returns an `error` without reconstructing or repairing the pointer. Because the CLI writes both files, divergence is an unexpected integrity condition rather than an agent-repairable gate.

Task-directory names keep the existing stable repository behavior: `task-<uuid4-hex>`. No timestamp or title-derived task-id format is introduced; readable title-derived names are confined to the separate artifact directory defined by its own ADR.

Project-local runtime state does not automatically migrate from the former `~/.workflow-harness` location. If a project has no `.workflow-harness/` runtime record, `wf start` creates a new source-backed state; the old user-level control-plane state is not treated as a fallback, source, or migration input.

Completed task directories under `tasks/` are never deleted automatically. A project may prune them manually if needed, because they are runtime audit records rather than operational storage burden.
