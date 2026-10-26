
# Agent Workflow Harness

This project is a deterministic control plane that lets an agent carry work through a fixed workflow without ever owning the state machine.

## Core vocabulary

- **Workflow** — the complete, closed-world definition of steps, transitions, and gates, expressed as YAML.
- **AWH** — the official abbreviation for agent-workflow-harness and the name of its CLI command. User requests such as “使用 awh 工作流完成 xxx” refer to this control plane and its `awh start` / `awh next` command protocol.
- **Step** — one named node in the workflow graph.
- **Guide** — the inline YAML instruction describing what to do when a step is entered successfully.
- **Gate** — a deterministic check blocking progression out of a step. v1 supports only file presence and command exit-code gates.
- **Transition** — one allowed edge from a non-terminal step to another step. The control plane selects exactly one transition when progression is granted.

- **Transition condition** — a deterministic boolean expressed as a narrow `when: <condition-variable> == <literal>` predicate on a candidate edge. The control plane evaluates it after the active step’s gates pass to select one outgoing transition. It never exposes alternative routes or future guides to the agent.

- **Condition variable** — the logical variable named directly by a narrow `when` predicate. It is resolved automatically by the control plane and is never declared, typed, or source-tagged in the transition itself; the underlying value may come from a runtime fact, start input, or another controlled resolver.

- **Runtime fact** — a value recorded by the control plane when it evaluates a generating workflow script or condition. The agent may produce the project evidence from which a fact is derived, but never writes the runtime fact or authoritative state directly.

- **Conditioned backedge** — an explicitly declared transition to an earlier step, selected by a transition condition only after the current step’s gates pass. It is a controlled reconsideration path, not an automatic route created by a gate failure.

- **Route selection record** — the control-plane audit record for one selected transition, including the active step, target step, condition variable, and resolved boolean value when relevant.

- **Backedge cycle limit** — the fixed safety cap of three uses for the same conditioned backedge within one task. A fourth attempt returns an `error` response rather than creating an unbounded repair loop.
- **Visited-step set** — the authoritative state projection of the steps entered during one task, used to determine whether a candidate route targets an earlier step.

- **Backedge count** — the authoritative per-transition count of conditioned backedge traversals stored in task state. The same source-to-target backedge may be selected three times; the fourth attempt is an error.

- **Conditional fact producer** — a workflow-package script that the control plane invokes lazily, after the active step’s ordinary gates pass, to create the runtime fact still needed to select one of that step’s candidate edges. It is not a normal step gate; malformed output or an operational failure is an `error`, not a `blocked` repair order.

- **Fact producer scalar protocol** — the strict output contract for heterogeneous condition values. A `workflow_script` must exit zero and print exactly one nonempty, single-line scalar after trimming whitespace; bare `true` or `false` is boolean, while every other value is an exact string. A `command` can express only boolean results: exit zero for `true`, exit one for `false`, and exit code two or greater for an evaluation error. Timeouts, extra lines, control characters, and malformed output are evaluation errors, never a valid false condition.
- **Start input** — a value supplied at task creation through a repeatable `--var name=value` argument, persisted by the control plane, and resolved indirectly by condition-variable name when needed. Start inputs are immutable while the task runs and are not written by the agent.
- **Condition variable resolution order** — the control plane’s fixed precedence for resolving a logical condition variable. If the active step declares a producer for that variable, the control-plane reruns the producer and records the result as the effective runtime fact. Otherwise it reads the existing runtime fact, then a start input, then the required workflow `WF_*` environment value. A still-unresolved variable is an evaluation error and never enables the default edge.

- **Environment condition alias** — the strict `WF_<UPPER_SNAKE_NAME>` environment key derived from a condition-variable name. It provides an operator or test override at lower precedence than task evidence and start input, while preventing a workflow from reading arbitrary environment variables.
- **Candidate-edge arbitration** — the control-plane rule that all candidate `when` edges of the active step are evaluated together and exactly one may resolve true. Multiple true edges are an error; if no conditional edge is true, the step’s single default edge is selected, or an error is returned when no default exists.
- **Unresolved condition variable** — a condition variable that cannot be resolved from a refreshed active-step producer, an existing runtime fact, a start input, or its required `WF_*` environment alias. It is an evaluation error and never makes the default edge available.

- **Condition evaluation error** — an operational failure to evaluate a route, including unresolved variables, producer timeouts, malformed producer output, multiple matching edges, or missing arbitration. It never advances the workflow and is distinct from a valid false condition.
- **Producer timeout** — the bounded maximum execution time for every conditional fact producer in a workflow. The default is 30 seconds; the workflow-level integer `producer_timeout_seconds` may set a value from 1 to 300. Exceeding the limit is an operational evaluation error, never a valid false condition.
- **Workflow graph integrity** — the static structural invariants checked before runtime: every step is reachable from entry, every non-terminal step has outgoing candidate edges and a path to terminal, terminal has no outgoing edge, self-loops and duplicate targets are rejected, and no source step contains duplicate predicates or multiple defaults.

- **Default edge** — the unconditional outgoing edge selected when no conditional edge resolves true. A step may declare at most one default edge, and a single transition cannot contain both `when` and `default`.
- **Step-local transition** — an outgoing candidate edge stored directly under its source step. It declares `to`, and optionally `when` or `default`, but never repeats the source step as `from`. Fact producers and route candidates for one step therefore live in the same place.

- **Workflow schema v2** — the workflow definition format identified by `version: v2`. It uses step-local transitions and step-local condition producers, accepts `awh start --var` task inputs, and no longer contains the top-level transition list used by v1.

- **Workflow schema v1** — the superseded linear definition with a top-level `transitions` list and exactly one outgoing edge per non-terminal step. It exists only as historical context; harness v2 does not provide runtime compatibility or automatic migration for v1 workflows or state.

- **Comparison literal** — the right-hand side of a narrow `when` predicate. A bare `true` or `false` literal denotes a boolean; every non-boolean literal is a single lowercase-or-uppercase ASCII token containing only letters, digits, dots, underscores, hyphens, or slashes, compared as an exact string.

- **Condition token rule** — the strict grammar for condition variables and string literals. Variables must be lowercase snake_case; literals exclude spaces, quotes, empty values, control characters, operators other than `==`, multiline text, regex, and all compound expressions.
- **Start-input token rule** — the strict CLI accept rule for `awh start --var`. Both the variable name and value must be single nonempty tokens, matching the route grammar; empty values, spaces, quotes, newlines, and control characters are rejected. Complex text judgment must instead be derived by a workflow script producer.
- **Task input resume contract** — when start matches the active alias and title, `--var` may be omitted or repeated exactly from task creation. Adding a new variable or changing an existing value returns `conflict`; it never mutates an active task’s inputs. Repeating the same variable in one command is an argument error.
- **Permissive start input admission** — `awh start --var` accepts any token-valid name/value pair, even when the current workflow does not statically reference that name in a `when` condition. Unused inputs remain persisted for audit and may become meaningful after a later compatible workflow restart, but they do not affect routing in the active workflow.

- **String condition value** — a condition value that is not true or false and is therefore compared byte-for-byte as text, without trimming, case folding, or semantic normalization.
- **Step-local fact producer** — a producer declared on the step whose outgoing edge may need the resulting fact. It runs only while that step chooses a route after its gates pass; it does not create a global variable namespace, and a logical condition variable may have at most one producer in a workflow.
- **Fact refresh rule** — the rule that when the active step declares a producer for a condition variable, the control plane reruns that producer before each route selection from that step and overwrites the variable’s runtime fact. For other steps, an existing runtime fact is read-only route evidence and the producer is not rerun.
- **Condition producer source policy** — condition producer scripts remain source-backed package assets rather than additional task-bound snapshots. Only `workflow.yaml` is fingerprinted and source-drift checked; producer scripts may change during the active task and each route selection executes the current package script.

- **Task input** — a condition-variable name and value admitted with the task at start time. It is immutable while the task runs and part of the task’s authoritative current state.

- **Current fact map** — the task-scoped collection of the latest runtime facts available for route decisions. It is control-plane authored and independent of the append-only history log.

- **Fact provenance** — the control-plane record of which step and producer generated a runtime fact, allowing the current value to be audited without reconstructing transitions from history.
- **Fact record** — the value and provenance stored for one condition fact. The record carries the current scalar value, producing step, producer type, and package-local producer reference; it does not store timestamps, stdout, or environment snapshots.
- **Agent workspace** — the target project directory where the agent reads workflow assets and produces stage artifacts.
- **Current-task pointer** — the minimal CLI-maintained `task.json` record in `.workflow-harness` that identifies the project’s single active task.
- **Task title** — the human- and model-visible semantic name for a task: a single concise English line of 5–120 characters using only ASCII letters, digits, spaces, and hyphens. The control plane trims and collapses whitespace, then matches the exact normalized title when resuming a task.
- **Task slug** — the deterministic directory-name form of a task title: lowercase ASCII letters and digits joined by single hyphens. The slug is truncated to 64 characters and followed by the complete task ID, so task artifact paths are readable and collision-free without relying on a probabilistic suffix.
- **Task artifact directory** — the project-local, task-scoped directory that holds workflow business artifacts, separate from the authoritative runtime state and audit log.
- **Template variable** — a `${name}` placeholder substituted by the control plane in model-facing instructions and parameterized gate inputs. Valid sources are limited to the built-in workflow and task artifact directories plus immutable task inputs; condition variables remain separate routing facts.
- **Task anchor** — the minimal CLI-maintained active-task projection at `.workflow-harness/task.json`, containing only `schema`, `task_id`, `workflow_alias`, and `title`.
- **Task preflight** — the skill-guided step where the agent reads the task anchor and decides whether the current request continues that task or requires a new workflow run.
- **Workflow creator** — the manual-only companion skill that turns a process design into a source-backed v2 workflow package, including its guide, gates, step-local routes, and condition producers. It is invoked only by an explicit creator request or a skill directive, and remains distinct from the thin runner skill, which executes a bound task’s control-plane commands.
- **Workflow creation destination** — the location selected for a newly authored workflow package. Project-local `.agents/workflows/<alias>/` is the default; user-level `~/.agents/workflows/<alias>/` is used only when the user explicitly requests cross-project reuse, and the built-in package catalog is not a creator output target.
- **Workflow validation command** — `awh validate <workflow-alias>`, a side-effect-free authoring command that statically checks a source-backed v2 workflow without creating or changing a task.

- **Workflow validation status** — the two-state result used by `awh validate`: `valid` or `invalid`, distinct from the five task-execution statuses returned by start, next, and decision commands.
- **Workflow creator write authorization** — the creator’s file-write rule. A new project-local package may be created directly after an explicit creator request, but modifying an existing package requires the user to approve the shown change scope; built-in packages are never creator-writable.

- **Workflow acceptance fixture** — a deterministic workflow bundle used to prove one or more harness capabilities before migrating a complete business flow. It is not itself the production replacement for the business workflow.
- **Workflow test fixture** — a workflow package stored under the repository test assets and copied into a temporary project during tests, rather than exposed in the built-in workflow catalog.
- **Route evaluation transaction** — the in-memory route-selection process that runs required step-local producers, resolves conditions, arbitrates edges, and checks the backedge limit. Only a successful route causes one atomic authoritative state write; any evaluation or arbitration error preserves the previous state.
- **Route selection privacy** — the audit rule that a successful route record names only the selected target and, when applicable, that edge’s condition variable, value, and source. Unselected candidate targets and their predicate results are not written to runtime files or returned to the agent.

- **Route evaluation phase** — the final part of `awh next` after every automatic gate and any active human gate have passed. The control plane refreshes required step-local facts, arbitrates candidate edges, records the selected route, and advances the task. Route facts are persisted only when the selected route completes successfully.

- **Start** — `awh start <workflow-alias> --task <title>`, which creates or resumes a task context and returns the current work order without evaluating gates or advancing state.
- **Next** — `awh next`, which evaluates the current gates and, only when they pass, advances to the next work order or terminal result.
- **Runtime state directory** — the project-local `.workflow-harness/` directory holding `task.json` and per-task state; it is readable but not agent-writable.
- **Runtime task directory** — the task-scoped `.workflow-harness/tasks/<task-id>/` directory holding authoritative `state.json` and the append-only `history.jsonl`.
- **Project directory** — the root used to identify a project and resolve relative gate paths and command-gate working directories; it defaults to the repository root and may be explicitly overridden.
- **Project key** — the namespace identity formed from a Unicode-safe project-name slug, two hyphens, and the first 16 lowercase hex characters of the SHA-256 digest of the resolved project path.
- **Workflow catalog** — the source-root resolution layer consisting of project workflows, user workflows, and built-in workflows.
- **Workflow alias** — the stable name used to select a workflow without exposing a workflow path.
- **Workflow package** — the source-backed directory, such as `<project>/.agents/workflows/<alias>` or `~/.agents/workflows/<alias>`, containing `workflow.yaml` and optional references, scripts, assets, or templates; the workflow graph remains control-plane owned, while other authored assets are model-readable and directly referenceable via `${workflowDir}`.
- **Stage brief** — the model-visible, free-form prose for the current stage, whether inline in YAML or as a package file; the framework performs exact single-pass substitution over the closed template-variable source set and does not parse, resolve, or inline transitive references.
- **Runner skill** — the domain-specific entry adapter that applies the command protocol and sequence-agnostic task discipline; it must not contain stage order, step-to-skill mappings, stage deliverables, complete gate lists, or the workflow graph.
- **Projection** — the current authoritative state derived from `state.json`, not from `history.jsonl`.
- **Fact source** — the authoritative runtime state recorded in `state.json`; `history.jsonl` records operational audit events but is not a recovery source.

- **Success** — the CLI advanced to the next step, or completed the workflow.
- **Blocked** — an active workflow cannot progress because its current gate has not passed; the response includes the current repair instruction and gate reason.
- **Error** — a workflow request cannot be interpreted due to an operational or validation problem.
- **Response status** — the agent-facing result state: `active`, `blocked`, `done`, `conflict`, or `error`.
- **Stage work order** — the minimal model-facing instruction for an active stage, excluding control-plane identities, step identities, and future stages.
- **Repair order** — the blocked response that repeats the active stage instruction with the failed gate and a concise, actionable reason.
- **Command gate excerpt** — the tail of a failed command’s stdout/stderr, stripped of ANSI escapes and trailing whitespace, limited to 1,500 Unicode characters and used as the reason for a blocked command gate.
- **Agent-blind interface** — the model-facing surface that exposes only the active work order, not the full workflow or future steps.
- **Done** — terminal success state; workflow has finished.
- **Human confirmation gate** — a step-exit gate that requires a recorded human decision before the control plane allows transition. In the local v1.2 scope it is audit evidence, not a hard proof that the decision came from a human.
- **Human decision record** — the control-plane record created by `awh approve` or `awh reject` for the sole human gate of the active step. It records the human decision and any rejection reason, but never advances the workflow.
- **Human decision command** — a model-facing command that records an approval or rejection for the active human gate and returns the current blocked state; it cannot advance a step by itself.
- **Human decision fingerprint** — the byte-exact aggregate fingerprint of the evidence paths listed by the human gate when a human decision was recorded. An approval passes only while those exact bytes remain unchanged.
- **Gate evaluation order** — the control-plane rule that all automatic gates run before the human gate. Human review is requested only after automated checks fail to block the step.
- **Human review point** — the workflow-determined boundary where a human decision is required within a specific stage, such as after requirements, after design, or before PR creation.
- **Human review request** — the explicit business question asked of the human for a human gate, preserved in the workflow and returned as the actionable review context.
- **Human review readiness** — the state in which every automatic gate on the active step has passed and the human decision is the only remaining blocker.
- **Human review reason** — the bounded `blocked.check.reason` string that carries the human request, evidence paths, and decision guidance without adding structured response fields.
- **Human rejection cycle** — the review loop created when a human rejects a step. It remains blocked until the evidence changes and a human approves the changed evidence.
- **Sticky rejection reason** — the latest rejection feedback that remains visible in the active blocked response until a newer human decision replaces it.
- **Human approval note** — optional reviewer context attached to an approval record; it is not required for the control plane to accept the approval.
- **Human decision history** — the immutable audit trail of approvals and rejections. Historical decisions remain inspectable but cannot satisfy gates in a later stage.
- **Human transition audit record** — the history-only metadata linking a transition to the human gate, decision, and evidence fingerprint that enabled it; it never appears in the model-facing response.
- **Human evidence path** — a relative project path whose content is fingerprinted when a human decision is recorded; it defines the artifact the human decision is bound to.
- **Human reason template** — the fixed single-line format the control plane uses to combine a human request, its evidence paths, and the decision commands into `blocked.check.reason`.
- **Human reason prefix** — the stable English status marker placed at the start of a human-gate reason, such as `HUMAN_REVIEW_PENDING` or `HUMAN_REVIEW_REJECTED`.

## Design mantra

> Workflow semantics reside in YAML and state authority resides in the control plane. The agent sees only work orders for the active stage.
