# Agent Workflow Harness — v1.1 Agent-Blind Local Control Plane

Status: ready-for-agent

## Problem Statement

The current v1 protocol exposes the entire workflow to the model. The agent must know a workflow YAML path or read a task snapshot to understand what to do; even skill-level instructions cannot reliably prevent the model from reasoning about future stages, transitions, gates, or from anticipating later artifacts. The workflow control plane is deterministic, but its model-facing surface leaks process semantics and encourages the agent to run ahead.

The user needs the model to receive only the work order for the active stage. The process contract must remain with a deterministic control plane, not with the agent’s judgment.

## Solution

Introduce a v1.1 agent-blind local control plane:

1. The model-facing protocol is `wf start <workflow-alias> --task <task-title>` followed by `wf next`.
2. Workflow aliases resolve internally to workflow definitions through a control-plane-owned catalog; the model never receives YAML paths.
3. Authoritative run state, snapshots, locks, history, and current-task pointers move out of the repository into a control-plane home keyed by project namespace.
4. The project repository contains only a small, ignored, agent-readable task projection containing the active task’s workflow alias and title.
5. The model receives one of five bounded response types: active, blocked, done, conflict, or error.
6. Active and blocked responses contain the active stage instruction. Blocked responses also identify the current gate and an actionable reason.
7. Gate evaluation, transitions, terminal completion, and audit remain entirely under control-plane authority.

The v1.1 goal is information minimization rather than a hard runtime security boundary. A determined agent with unrestricted filesystem access could still inspect local control-plane files. A trusted server, sandboxed control plane, or host-enforced permissions remain future work.

## User Stories

1. As a coding agent, I want a stable `wf start <workflow-alias> --task <task-title>` command, so that I can create a workflow task without receiving a workflow YAML path.
2. As a coding agent, I want `wf next` to accept no path arguments, so that I can continue the active project task without knowing where control-plane state is stored.
3. As a coding agent, I want the start response to contain the first stage instruction, so that I can immediately begin work after selecting a workflow.
4. As a coding agent, I want an active response to contain only the current stage instruction, so that I am not encouraged to plan around future stages.
5. As a coding agent, I want a blocked response to contain the current instruction and a gate reason, so that I can repair the active stage without reading workflow YAML.
6. As a coding agent, I want a done response to tell me that the task is complete, so that I stop issuing workflow commands and stop changing deliverables.
7. As a coding agent, I want a conflict response to identify the active task title and suggest safe next actions, so that I do not accidentally replace an existing project task.
8. As a coding agent, I want stable JSON output for every successful or erroneous path, so that I can reliably decide what to do next.
9. As a coding agent, I want an absence-of-work error that explains how to start a task, so that a fresh checkout does not leave me guessing.
10. As a coding agent, I want command-gate failures to include a bounded output excerpt, so that I can diagnose test or command failures without seeing the gate’s shell command.
11. As a workflow user, I want a task title, so that the current run has meaningful business semantics rather than only an opaque internal identifier.
12. As a workflow user, I want a project to have one active task at a time, so that parallel requests in the same project do not cause state confusion.
13. As a workflow user, I want an existing active task to be resumed when the requested workflow alias and task title match exactly, so that repeated start commands do not create duplicate runs.
14. As a workflow user, I want a request for a different task while one is active to conflict, so that the control plane cannot silently switch project context.
15. As a workflow user, I want the task title to remain concise, so that it is a stable identity anchor rather than an unrestricted requirement description.
16. As a workflow user, I want an agent-readable task projection at the project root, so that a workflow skill can inspect the active task title before choosing start or next.
17. As a workflow user, I want that projection to be control-plane-maintained and ignored by source control, so that local runtime state does not pollute commits.
18. As a workflow user, I want the projection rebuilt from the authoritative control-plane record when it is missing or altered, so that checkout and cleanup operations do not break an active task.
19. As a workflow user, I want the task projection deleted when the task reaches its terminal state, so that the absence of an active task can be represented without adding a completed status to the agent-facing schema.
20. As a workflow author, I want built-in workflow aliases to work without installation, so that standard delivery processes can be started immediately.
21. As a workflow author, I want user-installed workflow aliases to override built-in aliases, so that teams can customize standard processes without changing the package.
22. As a workflow author, I want an alias resolution error when no installed or built-in workflow matches, so that a misspelled alias cannot silently start the wrong process.
23. As a workflow author, I want each stage’s instruction to be the complete active-stage guidance, so that it explicitly states the work and artifacts to produce.
24. As an operator, I want workflow snapshots copied into the control-plane instance, so that an active run remains stable when workflow definitions change.
25. As an operator, I want a workflow lock recording the snapshot’s source and identity, so that each control-plane instance is bound to a specific workflow version.
26. As an operator, I want project directories resolved from the repository root, so that invoking the CLI from any subdirectory resolves the same project and executes gates deterministically.
27. As an operator, I want project namespaces to combine a readable project name segment with a hash of the resolved project path, so that local debugging remains practical while same-name projects remain isolated.
28. As an operator, I want a record of the full resolved project path in the namespace, so that I can inspect how the active state was originally bound.
29. As an operator, I want a repository task projection without a matching active control-plane task to produce an error, so that a project move or stale local file cannot silently discard a task.
30. As a developer, I want a control-plane home, so that workflow state is not stored in the agent working tree.
31. As a developer, I want the control-plane home to default to the user’s local home area, so that normal use requires no configuration.
32. As a developer, I want to override the control-plane home with an environment variable, so that tests and isolated environments do not share real project state.
33. As a developer, I want workflows organized by project namespace, so that control-plane storage scales across multiple projects.
34. As a developer, I want one current-task record per project namespace, so that control-plane lookup is simple and deterministic.
35. As a developer, I want task identity, current stage, workflow snapshot, and history to live in a control-plane instance, so that agent-visible artifacts are independent of authoritative state.
36. As a developer, I want exact normalized matching for workflow alias and task title, so that the control plane can reason deterministically rather than by semantic similarity.
37. As a developer, I want repeated start commands to resume the same active task without evaluating gates or advancing state, so that start cannot become a second progression path.
38. As a developer, I want gate progression to remain exclusive to next, so that only one command can advance the workflow.
39. As a developer, I want each next invocation to re-evaluate the active stage gates, so that the result always reflects the current project state.
40. As a developer, I want file-gate paths and command-gate working directories to resolve relative to the project directory, so that changing the caller’s subdirectory cannot alter workflow decisions.
41. As a developer, I want command-gate output stripped and bounded, so that a blocked response does not explode the model context with full command logs.
42. As a developer, I want command-gate reasons truncated by Unicode characters rather than bytes, so that multibyte text is not corrupted.
43. As a developer, I want the response contract to exclude task IDs, step names, transitions, workflow paths, gate lists, and future guides, so that the model-facing surface cannot leak process semantics.
44. As a developer, I want a clean breaking v1.1 interface, so that legacy workflow-directory arguments do not reintroduce exposed process paths.
45. As an operator, I want a concise event history, so that blocked attempts and successful transitions are auditable without relying on model narratives.
46. As an operator, I want existing tasks to complete through one active task per project, so that I can reason about what work is currently open.
47. As a workflow author, I want active-stage instructions to be the main process guidance surface, so that my task directions remain readable to both humans and agents.
48. As a workflow user, I want v1.1 to preserve the v1 closed-world state machine, so that the new interface does not introduce ad-hoc routing or runtime-defined stages.
49. As a workflow user, I want workflow definition validation retained, so that invalid states and transitions are rejected before a control-plane instance is created.
50. As a reviewer, I want a small fixed set of response statuses, so that shell expectations and skill prompts do not proliferate.

## Implementation Decisions

- V1.1 is an information-minimization release, not a hard security boundary. A later trusted control plane can provide real inaccessible state.
- The v1 `--workflow` and `--task-dir` protocol is removed cleanly. Existing v1 task directories are historical records and are not automatically migrated.
- The agent-facing commands are exactly `wf start <workflow-alias> --task <task-title>` and `wf next`.
- `start` either creates the first control-plane instance for the project or resumes the active instance when the resolved alias and task title match exactly.
- `start` never evaluates gates or advances a stage. It returns the active instruction for the current stage.
- `next` evaluates the active stage gates. If a gate fails, it returns a blocked repair order. If all gates pass, it advances at most one transition and returns the newly entered instruction or terminal result.
- A project may have only one active workflow task at a time.
- A request to start a different alias or title while another task is active returns `conflict`.
- A task title is required, must be one line, must contain 5–120 characters after trimming, and has internal whitespace collapsed before exact comparison.
- Workflow aliases are stable names, not paths. They are resolved through a user catalog that takes precedence, followed by a built-in catalog bundled with the harness.
- Built-in standard workflow aliases remain usable without installation. User-installed workflows can override or extend them.
- The control-plane home defaults to `~/.workflow-harness/` and can be overridden with the `WF_HOME` environment variable.
- Control-plane storage is organized by project namespace, project current-task record, and individual task instances.
- A project directory is resolved by explicit project override first, then repository root, then current directory outside a repository.
- File gates and command-gate working directories resolve relative to the project directory. Calls from any subdirectory of the same project produce the same result.
- The project namespace key is a readable Unicode-safe project-name slug followed by the first sixteen lowercase hexadecimal characters of the SHA-256 digest of the resolved project path.
- The project namespace records the resolved project path for human inspection.
- The authoritative project current-task record identifies the active internal task identity. The model never receives that internal task identity.
- The project repository contains an ignored control-plane projection containing the active workflow alias and task title.
- The task anchor is readable but not authoritative. The CLI rebuilds it whenever the authoritative current-task record exists.
- A missing or altered task anchor is repaired from the authoritative record. If no active task exists but the anchor exists, the CLI reports an error rather than deleting the anchor or starting a new task.
- The task anchor is deleted when the task reaches its terminal state. Control-plane history remains available for audit.
- The active response contains only status, task title, and current instruction.
- The blocked response contains status, task title, current instruction, failing gate, and concise reason.
- The done response contains status and task title.
- The conflict response contains status, active task title, reason, and an optional safe next-action hint.
- The error response contains status, reason, and an optional safe next-action hint.
- Responses never include task IDs, step names, transitions, workflow paths, complete gate lists, future guides, state paths, or history paths.
- The five top-level statuses are exactly `active`, `blocked`, `done`, `conflict`, and `error`.
- `wf next` with no active task returns `error` with a reason explaining that no active workflow task exists, plus a start hint.
- Command gates execute with the project directory as their working directory.
- Failed command gates produce a reason derived from combined standard output and standard error, not from the gate’s command definition.
- Command-gate reasons strip ANSI escape sequences and trailing whitespace, preserve multi-byte character boundaries, retain at most the final 1,500 Unicode characters, and mark truncation.
- If a failed command yields no output, the reason is a fixed no-output message.
- Active and blocked responses do not include a separate expected-outputs field. The active stage instruction must itself state what work and artifacts are required.

The response contract is decision-rich enough to preserve as a prototype-derived shape:

```json
{
  "status": "active | blocked | done | conflict | error",
  "task": {
    "title": "修复登录超时"
  },
  "instruction": "Current stage instruction",
  "check": {
    "gate": "gate-id",
    "reason": "Actionable reason"
  },
  "active_task": {
    "title": "修复登录超时"
  },
  "reason": "Human-readable conflict or error reason",
  "hint": "Optional safe next action"
}
```

Only the fields matching each response status are emitted.

## Testing Decisions

- The primary test seam is the process-level CLI boundary through black-box subprocess invocation.
- Good tests assert only externally observable behavior:
  - process exit code,
  - parsed JSON stdout,
  - the agent-readable project task projection,
  - and persisted control-plane artifacts visible as public local storage.
- Tests should not assert internal parser, helper, or storage-class signatures.
- Tests must isolate the control-plane home and create temporary projects rather than using the developer’s real home or repository.
- Existing black-box CLI tests provide the prior art: they invoke the workflow command as a subprocess, parse its stable JSON contract, and inspect persisted task state.
- The same process-level seam should cover:
  1. starting a new task and receiving the first active instruction;
  2. resuming an existing task with the same alias and title without gate evaluation;
  3. rejecting a different alias or title with conflict;
  4. returning no-active-task error from next;
  5. returning blocked repair responses with the current instruction and gate reason;
  6. handling command-gate output, truncation, no-output, and multibyte boundaries;
  7. advancing exactly one stage when gates pass;
  8. reaching terminal state and deleting the repository task projection;
  9. rebuilding a missing or altered repository task projection when authoritative active state exists;
  10. returning an error when a task projection exists without active control-plane state;
  11. resolving the same project and same gate result from a subdirectory;
  12. overriding a built-in workflow alias with a user-installed alias;
  13. rejecting invalid aliases, invalid task titles, malformed workflow definitions, and legacy arguments;
  14. preserving the control-plane snapshot after a source workflow changes;
  15. recording blocked and successful transitions in control-plane history.
- The response contract tests should explicitly check that task ID, step name, transition, YAML path, full gate list, and future guide fields are absent.
- The command-gate output tests should use commands that emit Unicode text, empty output, and output longer than the response limit.
- All workflow path and project-dir resolution tests should pass `WF_HOME` as an isolated environment value.

## Out of Scope

- A trusted server, MCP control plane, host sandbox, or real filesystem permission boundary.
- Stage tokens or other anti-fabrication evidence schemes.
- Conditional routing, parallel workflow paths, or multiple active project tasks.
- Automatic reinstallation or migration of v1 task directories.
- Automatic project rebinding after the local project path changes.
- A separate expected-outputs response field.
- Human approval workflows.
- External database storage.
- A web UI.
- A workflow alias management user interface.
- Cancelling, archiving, listing, selecting, or repairing historical project tasks.
- The kind of security guarantee that could stop a determined agent with unrestricted local filesystem access.

## Further Notes

- V1.1 should be treated as a clean breaking change because the new control-plane model replaces rather than augments the v1 task-directory protocol.
- The project task projection and control-plane current-task record intentionally serve different purposes: one is a readable semantic anchor for a workflow skill; the other is authoritative state.
- The design keeps semantic judgment with the agent and deterministic progression authority with the control plane. A skill may read the task projection and choose an existing title, but the CLI still matches that title deterministically.
- A later trusted control plane can replace the local control-plane home while preserving the same agent-facing commands and response contract.
- The later roadmap should progress from v1.1 information minimization, to v1.2 lifecycle and operability, then stronger verification with stage tokens, and finally a trusted control-plane service.
