# Agent Workflow Harness — v1 Spec

Status: ready-for-agent

## Problem Statement

A coding agent working across a large task must not be trusted to decide when it has finished a stage, or to choose which stage to enter next. Without an external control plane, progress becomes probabilistic and hard to audit. The user needs a generic mechanism that separates workflow semantics from agent judgment, so an agent can be productive while a deterministic framework owns the state machine.

## Solution

A small, host-agent-agnostic framework that:

1. declares a workflow as an explicit, closed-world YAML state machine;
2. creates a self-contained task directory for one workflow run;
3. copies the workflow snapshot into that task directory during initialization;
4. exposes exactly one command, `wf next`, which decides whether the current step may advance;
5. executes deterministic gates and refuses progression if they fail;
6. returns stable JSON describing success, failure, or completion.

The agent does not own the state machine. It can only request progression by invoking the single command.

## User Stories

1. As a workflow author, I want to define steps and transitions in YAML, so that I can represent a deterministic process without writing an imperative controller.
2. As a workflow author, I want gates to be optional, so that simple steps can advance without an unnecessary gate.
3. As a workflow author, I want each step to include an inline guide, so that the successful move to the next stage tells the agent what to do.
4. As a workflow author, I want a terminal step, so that the workflow has a clear completion point.
5. As a workflow author, I want the workflow to be a closed-world graph, so that the agent cannot invent new stages.
6. As a workflow author, I want every non-terminal step to have exactly one outgoing transition, so that there is no ambiguity or branching in v1.
7. As a workflow author, I want YAML validation to fail when a step has multiple outgoing transitions, so that invalid workflows are rejected at initialization.
8. As a workflow author, I want the workflow snapshot copied into the task directory, so that one workflow run is stable even if the source YAML is later edited.
9. As a workflow author, I want a lock file to bind the task directory to the workflow snapshot, so that each run is uniquely associated with one workflow version.
10. As a workflow author, I want Python as the implementation language, so that I can iterate quickly and rely on straightforward subprocess and YAML handling.
11. As a developer, I want a single CLI command, so that the workflow interaction surface is easy to reason about and hard to misuse.
12. As a developer, I want every call to be a gate re-attempt, so that success always reflects the current filesystem, not a stale memory of an earlier call.
13. As a developer, I want a stable JSON success object, so that agents and tools can programmatically interpret progression.
14. As a developer, I want a stable JSON failure object, so that blocked progression is unambiguous.
15. As a developer, I want the failure object to omit the guide, so that failure does not masquerade as a next-step instruction.
16. As a developer, I want the success object to include the next step’s guide, so that progressive work is specifically guided after each successful transition.
17. As a developer, I want a terminal step to yield `done: true`, so that completion is explicit and does not require inventing a separate completion mode.
18. As a developer, I want each step’s guide to live inline in YAML, so that the workflow file is the complete source of truth.
19. As a developer, I want gates to be ordered and fail-fast, so that I can identify the principal blocking validation point without parsing a long combined report.
20. As a developer, I want each workflow run to use its own task directory, so that long-running work is self-contained and restartable.
21. As a developer, I want each task directory to store the workflow snapshot, so that later changes to the original YAML do not alter an in-flight task.
22. As a developer, I want a local event log, so that I can reconstruct what happened without relying on the agent’s own narrative.
23. As a developer, I want a derived state object, so that the current step is cheap to read on each invocation.
24. As a developer, I want the event log to be the authoritative fact source, so that the state object can be rebuilt or validated after corruption.
25. As a developer, I want all workflow files to live under a single root, so that the project is easy to understand and portable.
26. As a developer, I want to use an external database, so that the framework can scale beyond one directory.
27. As a developer, I want the framework to be host-agent-agnostic, so that I am not locked to Codex or Claude.
28. As a developer, I want the workflow interpreter to run outside the coding agent, so that the model cannot influence state by merely producing text.
29. As an operator, I want a repository built around one workflow control plane, so that all progress decisions are uniformly governed.
30. As an operator, I want the framework to generate a clear, minimal history event per attempt, so that repeated failures are traceable without massive logs.
31. As an operator, I want to see which gate failed, so that I can diagnose why a workflow could not progress.
32. As an operator, I want the framework to fail fast, so that repeated invocations do not produce large mixed reports.
33. As an operator, I want the control plane to reject an invalid workflow during initialization, so that it never runs with unresolvable states.
34. As an operator, I want the workflow to support one active instance per directory, so that concurrent runs remain isolated.
35. As an operator, I want to be able to inspect the workflow state with the same command I use to progress, so that the system has one protocol, not many.
36. As an operator, I want a straightforward CLI naming convention, so that the framework is discoverable and memorable.
37. As an operator, I want the framework to include an explicit issue tracker convention, so that future work can be triaged without ad-hoc decisions.
38. As an operator, I want to record architecture decisions persistently, so that future contributors understand exactly why the v1 design is this specific.
39. As an operator, I want the framework to explicitly reject permissions-style constraints in v1, so that I do not mistake advisory rules for real enforcement.
40. As an operator, I want the framework to omit complex evidence schemas in v1, so that failure reasons stay legible rather than becoming a full audit system.
41. As an operator, I want out-of-scope boundaries documented, so that future contributors do not casually broaden the project.
42. As an agent, I want to request the next action with one command, so that I can avoid guessing whether a workflow has advanced.
43. As an agent, I want clear failure reasons, so that I can correct the specific blocker and try again.
44. As an agent, I want the guide for the next stage only after success, so that I do not confuse a blocked stage with the next stage.
45. As an agent, I want a terminal completion state, so that I know exactly when to stop.
46. As an agent, I want stable JSON input and output, so that I can parse results reliably.
47. As an agent, I want no hidden or conditional access paths, so that every workflow step is driven by the same explicit command.
48. As a reviewer, I want black-box tests around the primary CLI seam, so that internal changes do not break the user-facing contract.
49. As a reviewer, I want tests that verify a workflow can advance step by step, so that the state machine is validated end to end.
50. As a reviewer, I want explicit acceptance status for issues, so that work readiness is visible without reading implementation details.

## Implementation Decisions

- The framework is a **host-agnostic CLI** rather than a host-agent-specific plugin.
- The only public workflow interface in v1 is the **`wf next`** command.
- Workflow semantics are defined in a **closed-world YAML state machine**.
- Every non-terminal step has **exactly one outgoing transition**; conditional routing is out of scope.
- The workflow snapshot is **copied into the task directory** during initialization, alongside a lock file that identifies the source workflow and its hash.
- The step guide is stored **inline in YAML**, is required for every non-terminal step, and is emitted only when the step advances successfully.
- `gates` is an **optional** field; an omitted or empty `gates` list means the step has no progression gate.
- Gate primitives are deliberately limited to **file existence** and **command exit-code**.
- Gate evaluation uses **fail-fast** ordering: the first failed gate terminates evaluation.
- Gate results are **reason-only**; stdout, stderr, evidence trees, and structured gate result files are intentionally not produced in v1.
- The CLI accepts the workflow path only on the first invocation, then binds the task directory to the copied snapshot.
- The control plane returns only two top-level result kinds: **success** and **failed**.
- Success messages always include the **next step’s guide**.
- Failure messages always include the **failed gate**, the current step, and a concise reason; they omit the guide.
- Terminal transitions return **`done: true`** without requiring a separate workflow status mode.
- Each workflow invocation starts from the current derived state and re-runs gates; it does not trust a previous success.
- The event log is **append-only history** and is the fact source; state is a derived projection.
- History records successful transitions and blocked attempts with only the minimum fields needed to understand progression.
- The task directory contains all runtime context: workflow snapshot, lock file, state projection, and history log.
- The framework does not generate runtime code and does not require an external database.
- V1 is implemented in **Python** for speed of iteration, straightforward YAML handling, and easy subprocess invocation.
- The repository includes a local Markdown-based issue tracker convention and architecture decision records.
- The system will not create separate guide files, evidence directories, or permission manifests.
- The system will not enforce action boundaries inside the coding agent host in v1; its authority is solely over workflow progression.
- The framework is intentionally **not** a general-purpose proof system, testing framework, or process platform.

## Testing Decisions

- The primary test seam is the **external CLI boundary**.
- Good tests assert only the observable public contract:
  - the command’s exit status,
  - the stable JSON result,
  - the resulting task-directory state,
  - and the history log.
- Tests must not assert internal parser, loader, or helper-function signatures.
- The same seam must cover:
  1. initial invocation with a workflow and task directory,
  2. successful gate execution,
  3. successful progression to the next step,
  4. failure with reason-only output,
  5. terminal completion with `done: true`,
  6. repeated invocation on unchanged work,
  7. and preservation of the workflow snapshot across invocations.
- Prior art is minimal because this is a new project; the first tests should therefore define the canonical contract rather than mirror an existing pattern.
- The intended test style is behavior-driven and fixture-based, with small workflow YAML examples exercised through the command-line interface.

## Out of Scope

- Conditional transitions
- Parallel transitions
- Multiple outgoing transitions from one non-terminal step
- Agent prompt‑enforcement or permissions
- Workflow policies such as allowed or forbidden file actions
- Evidence archives or raw command output capture
- External database storage
- Host-specific hooks or interceptors
- Runtime-defined workflows
- Automatic workflow upgrades after task initialization
- A web UI
- A general issue tracker integration beyond the documented local Markdown convention

## Further Notes

- The workflow control plane deliberately lacks two abilities that future versions may add: conditional routing and richer gate evidence.
- The design goal is not to make the model “behave”; it is to make **progression** impossible when the declared workflow requirements are unmet.
- The workflow semantics are influenced by the user’s broader methodology of “cognition for the model, state for deterministic code.”
- Example workflows use the illustrative delivery vocabulary **clarify**, **spec**, **code review**, and **pull request**. These stage names are examples, not part of the framework’s required vocabulary or core contract.
- No code module paths are specified here because implementation has not yet begun. The only stable interface is the command itself.
