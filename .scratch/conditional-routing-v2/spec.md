# Conditional routing and workflow creation v2

Status: ready-for-agent

## Problem Statement

The harness currently enforces a single outgoing edge for every non-terminal step. A workflow author cannot express conditional routes such as “continue with technical-contract clarification only when the architecture split contains a cross-application contract” or “return to architecture split when routing evidence is incomplete.” This forces real processes such as PRD-to-Spec into either multiple near-duplicate workflows or artificial terminal stages.

The current authoring experience is also too manual. A workflow author must edit YAML and package files directly and can only discover graph errors by starting a task. There is no dedicated, hand-invoked workflow creator skill and no side-effect-free validation command. The harness therefore needs a deterministic conditional-routing model that preserves agent-blind progression, plus a workflow-creation interface that remains separate from the thin runner skill.

## Solution

Introduce workflow schema v2 and task-state v2 as a direct successor of the current formats. A non-terminal step owns its candidate outgoing edges and, where needed, the step-local condition fact producers required to select one of those edges. The control-plane CLI remains the only writer of runtime facts, route selection, and progression state. The agent continues to receive only the selected stage’s work order and never sees alternative routes or future guides.

Add a strict condition language based on a single equality predicate. Resolve condition variables from control-plane-owned values: an active-step producer, an existing runtime fact, a start input, or a required environment alias. Support boolean and exact-string comparisons. Route selection uses exact arbitration: all evaluated conditions are considered together, exactly one conditional edge may match, and a declared default edge is selected only when all conditions successfully evaluate false.

The release also adds a static workflow validation command, a manual workflow-creator skill, and a deterministic PRD-to-Spec routing acceptance fixture. It is a clean v2 release: v1 workflows and active v1 task state are not runtime-compatible or automatically migrated.

## User Stories

1. As a workflow author, I want workflow schema v2, so that I can define candidate routes instead of one fixed successor for every step.
2. As a workflow author, I want each step to own its outgoing edges, so that route and staging logic stay together.
3. As a workflow author, I want a source step to contain its guide, gates, condition producers, and candidate routes, so that I do not have to reconcile fragment definitions across a global transition list.
4. As a workflow author, I want a candidate transition to name only its target and route condition, so that the source step is not repeated in every edge.
5. As a workflow author, I want a default edge, so that one route can explicitly represent the expected fallback when no conditional route matches.
6. As a workflow author, I want `when` and `default` to be mutually exclusive on one transition, so that an edge cannot combine fallback and conditional semantics.
7. As a workflow author, I want at most one default edge per step, so that fallback arbitration is unambiguous.
8. As a workflow author, I want condition literals to support true and false, so that simple boolean routes remain readable.
9. As a workflow author, I want non-boolean condition literals to be compared as exact strings, so that I can use route categories such as entry modes or risk levels without inventing a type system.
10. As a workflow author, I want the condition grammar restricted to one equality predicate, so that I can inspect routing logic without reading a nested expression language.
11. As a workflow author, I want condition variables to use a stable lowercase name, so that producer and edge references remain predictable.
12. As a workflow author, I want the target step to be statically validated, so that a workflow cannot start with a route to an undeclared step.
13. As a workflow author, I want the workflow version to clearly identify v2, so that readers know which route semantics apply.
14. As a workflow author, I want no top-level transition list in v2, so that no workflow can have two competing definitions of graph order.
15. As a workflow author, I want step-local fact producers, so that a fact can be generated from the evidence of the step that needs to route from it.
16. As a workflow author, I want at most one producer per logical condition variable in a workflow, so that the same variable cannot mean different things at different stages.
17. As a workflow author, I want producers to run only after all automatic gates pass, so that route logic cannot request artifact judgments before the stage is complete.
18. As a workflow author, I want producers to run only after any human gate passes, so that routing does not begin while stage evidence is still pending review.
19. As a workflow author, I want an active-step producer to rerun before each route selection from that step, so that backedges re-evaluate repaired evidence.
20. As a workflow author, I want later steps to read a previously recorded runtime fact, so that repeated stages can use the same control-plane fact without rerunning the original producer.
21. As a workflow author, I want start inputs to be admitted through repeatable task-creation variables, so that a caller can provide route context at task admission.
22. As a workflow author, I want start inputs to allow token-valid names that the active graph does not reference, so that stable task arguments remain useful after later workflow evolution.
23. As a workflow author, I want start input values to be persisted as raw strings, so that the original caller intent remains inspectable.
24. As a workflow author, I want start input values to be preserved on resume, so that an active task cannot silently change route conditions.
25. As a workflow author, I want a required environment alias to act as an explicit operator override, so that tests and operators can force a route without editing project state.
26. As a workflow author, I want same-name environment access restricted to the required uppercase alias, so that a workflow cannot read incidental surrounding process variables.
27. As a fact producer author, I want a workflow script producer to output exactly one scalar, so that a producer result is unambiguous.
28. As a fact producer author, I want a command producer to express only boolean results, so that shell exit status cannot masquerade as a string value.
29. As a fact producer author, I want malformed output, producer failure, and timeout to return an operational error, so that the harness never interprets evaluation failure as false.
30. As a fact producer author, I want a workflow-level producer timeout, so that route evaluation cannot hang indefinitely.
31. As a fact producer author, I want a default 30-second timeout, so that simple bounded evidence checks require no additional configuration.
32. As a fact producer author, I want the workflow timeout to be configurable within a bounded range, so that a legitimate heavier bounded check can be accommodated.
33. As a workflow author, I want all candidate `when` edges to be evaluated together, so that declaration order cannot act as hidden route priority.
34. As a workflow author, I want multiple matching edges to be an error, so that ambiguous routing is detected.
35. As a workflow author, I want no matching conditional edge to fall back to the default edge, so that expected fallback behavior is explicit.
36. As a workflow author, I want an unresolved condition variable to be an error, so that a missing route input never silently becomes false.
37. As a workflow author, I want an explicit step-to-earlier-step edge, so that a process can reconsider an upstream stage after later evidence is inspected.
38. As a workflow author, I want backedges to be ordinary declared transitions, so that recovery remains part of the closed graph and not hidden outcome routing.
39. As a workflow author, I want a fixed three-use backedge limit, so that recursive evidence failure cannot create an unbounded repair loop.
40. As a workflow author, I want the fourth attempt of the same backedge to return an error, so that the operator can intervene before the process loops indefinitely.
41. As an operator, I want backedge counts in authoritative state, so that route limits remain active after CLI restart.
42. As an operator, I want route history to record only the selected edge, so that audit remains useful without exposing all possible future paths to an agent.
43. As an operator, I want route history to record the selected condition variable, resolved value, and source, so that I can audit why a route was selected.
44. As an operator, I want backedge history to include the selected source and target, so that I can identify a stuck reconsideration path.
45. As an operator, I want an exhausted backedge error to preserve the current state, so that an erroneous route count cannot silently alter workflow progress.
46. As a coding agent, I want the response schema to remain minimal, so that I can continue to parse the existing execution statuses even after conditional routing is introduced.
47. As a coding agent, I want only the selected stage instruction in the response, so that seeing a backedge does not invite me to plan an alternative route.
48. As a coding agent, I want route errors expressed through the existing error status and a bounded reason, so that I do not confuse producer failure with an actionable blocked repair.
49. As a coding agent, I want the runner skill to stay protocol-thin, so that it does not learn business graph rules or condition semantics.
50. As a workflow creator user, I want a manually invoked creator skill, so that process design does not start automatically whenever I merely mention workflow progress.
51. As a workflow creator user, I want the creator skill to produce a complete runnable source package, so that I can hand a coherent workflow to the runner.
52. As a workflow creator user, I want project-local workflow package creation as the default, so that project-specific workflows stay under version control.
53. As a workflow creator user, I want a user-level package only on an explicit cross-project request, so that globally reusable workflows are not created by accident.
54. As a workflow creator user, I want the creator to reject built-in package writes, so that standard catalog changes remain product releases rather than local creation side effects.
55. As a workflow creator user, I want a new project-local package to be created directly after explicit invocation, so that starting a new workflow package does not require a redundant extra confirmation.
56. As a workflow creator user, I want the creator to show the affected scope before modifying an existing workflow package, so that it does not overwrite operational process assets.
57. As a workflow creator user, I want the creator to validate a generated or changed package, so that I can iterate without starting a task.
58. As a workflow maintainer, I want a side-effect-free validation command, so that I can check a workflow package without altering a project, task, source fingerprint, or history.
59. As a workflow maintainer, I want static graph integrity checks, so that unreachable steps and dead-end branches are rejected at validation.
60. As a workflow maintainer, I want the graph to preserve its closed-world property, so that all destinations and recovery paths remain declared.
61. As a PRD-to-Spec integrator, I want a deterministic routing acceptance fixture, so that I can prove the harness can express the associative process condition logic.
62. As a PRD-to-Spec integrator, I want an entry-mode fixture route, so that confirmed-prd and ordinary-prd entry semantics can be exercised.
63. As a PRD-to-Spec integrator, I want a technical-contract fixture route, so that a yes-no fact producer can select conditional clarification.
64. As a PRD-to-Spec integrator, I want a routing-gap fixture backedge, so that an incomplete route returns architecture split for reconsideration.
65. As an operator, I want a direct v2 upgrade, so that stale old-format state is not used to simulate a migrated, compatible workflow.
66. As an operator, I want a clear error when I try to continue an old v1 active task under the new runtime, so that I can inspect evidence and explicitly start a replacement task.
67. As a workflow maintainer, I want the accepted accepted fixture under test assets, so that a synthetic graph does not become a production catalog entry.
68. As an operator, I want active-task state to remain the authoritative route source, so that modifying audit history cannot alter progression.
69. As a workflow maintainer, I want permissive start inputs to remain bounded tokens, so that task arguments cannot become a second business-content payload.
70. As a workflow maintainer, I want producer resolve source trusted over immutable start inputs on an active producer step, so that actual post-gate evidence takes precedence.
71. As a workflow maintainer, I want a workflow-creation path and a task-runner path represented by separate skills, so that process design and execution do not contaminate each other.
72. As a reviewer, I want external route results to be reproducible from static package definitions, so that I can understand why a step advanced without running the coding agent.

## Implementation Decisions

- Workflow v2 is a direct replacement of the current definition format and route semantics. It accepts only version v2 definitions, global graph identity (`entry`, `terminal`, and the complete step map), and no top-level transition list.
- Each non-terminal step owns a nonempty list of candidate transitions. Each candidate names its target. It selects one of a condition predicate or the default route, never both. No transition repeats its source step.
- The condition language is a single equality predicate of the form `<condition-variable> == <literal>`, permitting no conjunction, disjunction, negation, nesting, regex, or free-form shell interpolation.
- Condition variables are lowercase snake-case names. A string literal is a single token composed of letters, digits, dots, underscores, hyphens, or slashes. A bare `true` or `false` literal denotes a boolean; any other string literal is compared exactly without trimming, case folding, or semantic normalization.
- Start inputs are admitted at task creation using repeatable `--var name=value`. Names and values are single tokens, and neither empty nor multiline. Values remain raw strings in state, even when a comparison later normalizes true or false.
- Task admission is permissive: an input not statically referenced by the active graph is accepted and persisted for audit and future workflow evolution. It has no route effect unless a graph condition references it.
- An active task can be resumed when variable are omitted or repeated exactly as originally written. Adding a new variable or changing an existing value returns a conflict. Duplicate use of one variable name in one command is an error.
- Condition resolution is control-plane only. On a step that declares a producer for the needed condition variable, the CLI reruns the active-step producer and records its result as the effective runtime fact. Otherwise the CLI resolves the variable from the existing runtime fact, then start input, then the strict uppercase environment alias. A still unresolved variable is an evaluation error and never selects the default edge.
- Environment aliases are inferred only from a condition-variable name using a fixed uppercase name pattern. Ambient environment values are not treated as task facts and are not persisted in state.
- Fact producers are declared on the step whose outgoing edges need the fact. A logical condition variable has at most one producer in the entire workflow.
- Producer execution happens after every automatic gate and the step’s human review gate, if any. `approve` still only records human intent; it does not execute a producer or advance the stage.
- Active-step producers execute before each route selection from that step. Later steps read the recorded runtime fact and do not recall a producer owned by an earlier step.
- Producer execution order and status are:
  1. automatic gates;
  2. human review;
  3. active-step fact producers;
  4. candidate edge arbitration;
  5. route history append and authoritative state progress.
- A `workflow_script` producer exits zero and emits exactly one nonempty single-line scalar. Any nonempty line that is not bare `true` or `false` is persisted and compared as an exact string. Extra lines, control characters, non-zero exit, malformed output, or timeout are operational errors.
- A `command` producer supports only Boolean semantics: exit zero resolves true, exit one false, and exit two or greater error. Its stdout is not a fact value.
- The workflow may include one integer `producer_timeout_seconds`. The default is 30 and accepted values are 1 to 300 inclusive. It applies to every condition producer in that workflow.
- All candidate `when` edges of the active step are considered together. Exactly one may resolve true. Zero true edges select the single default route if one exists; a zero-true condition set with no default form is an error. Two or more true edges form an error.
- A transition to a non-current step already present in the task’s visited set is a backedge. Backedges are explicit ordinal route candidates, not gate-failure outcomes.
- A dynamic backedge transition is counted in authoritative task state. The same source-target transition may be selected three times; the fourth attempt is an error. The backedge limit is not exposed as per-edge configuration.
- Route evaluation is a logical state transaction. Required producer outputs are held in memory until producer arbitration and the backedge limit all succeed. Any error leaves the current step, runtime facts, visited steps, and counter state unchanged.
- Runtime state v2 is the authoritative route source. It stores immutable inputs, latest condition facts with provenance, the task visited set, and backedge counters. It does not store output capture, producer stdout, environment values, or time data.
- The active-task pointer remains intentionally unchanged and does not hold fact or route state.
- Runtime facts are control-plane-authored. The agent may influence project evidence the script inspects, but cannot directly write runtime state, conditions, route counters, or per-step history.
- A workflow v2 state update is a single atomic write that advances the current step, records accepted facts, updates visited steps, and updates backedge counters together.
- History persists only a successful route's selected source and target, the condition variable, resolved value, and resolve source, or the default route marker. Backedge route records add the selected source-target backedge count. Losing edges and candidate router truth values are not recorded.
- Static workflow validation is a side-effect-free authoring command that resolves a workflow package through the normal alias precedence and reports only `valid` or `invalid`.
- `wf validate` does not create a task, bind a workflow fingerprint, read the active pointer, execute gates, execute producers, or write runtime state. It checks grammar and static closed-world graph integrity. The two-state validation response is separate from the five normal execution statuses.
- Graph validation requires:
  * every step reachable from entry;
  * every non-terminal step has candidate edges and a static path to terminal;
  * terminal has no outgoing edges;
  * no self-loops;
  * no duplicate candidates on a source step;
  * each step has at most one default;
  * a candidate cannot contain both a condition and the default marker;
  * one candidate cannot use an unsupported operator;
  * all candidate targets exist;
  * declared producer paths remain inside the package and project-argument paths remain inside the project.
- The existing built-in workflow packages move directly to v2. There is no parallel v1 parser in the new runtime.
- Active v1 task state is not automatically migrated. On encountering old state, the new runtime returns an error; the operator can inspect evidence and start a replacement v1-to-v2 task when ready.
- Workflow scheduling path selection remains fully in the control plane. The agent-facing response contract is otherwise unchanged and still uses the existing active, blocked, done, conflict, and error statuses.
- Backedge and route audit are not authoritative. History remains append-only for audit and never serves as a recovery or source of truth.
- Producer scripts remain source-backed like other workflow package assets. The active task continues to fingerprint only the workflow authoring definition. A producer script that changes while a task is active is executed with its current package contents.
- A future decision-model producer, such as a small constrained decision system, is reserved as a new controlled value provider behind the same scalar condition-variable interface. This release does not implement probabilistic, LLM, or live external-decision integration.
- Workflow creation and task execution use separate skills:
  * the runner is a manual-adjacent thin protocol skill, invoked for task progression and retaining no business graph or condition rules;
  * the workflow creator is exclusively explicit-invocation and cannot auto-trigger from ordinary task continuation language.
- The workflow creator defaults to producing project-local packages. User-level packages are allowed only on explicit cross-project request. Built-in packages remain non-writable by the creator.
- The creator can create a new project-local package directly after explicit invocation, and it shows the change scope and gets user approval before overwriting an existing workflow package.
- The v2 acceptance model is a deterministic PRD-to-Spec routing fixture under test assets. It serves only acceptance; it is not a replacement for a production PRD-to-Spec workflow. It is copied into a temporary project's source-backed package for tests, and is not installed into the built-in runtime catalog.

## Testing Decisions

- The release uses one primary external seam: the CLI process boundary. The CLI `validate`, `start`, `next`, `approve`, and `reject` commands are invoked as child processes in isolated project environments.
- The primary seam is the highest available external boundary to the current harness. Tests do not drive internal workflow parser, runtime, storage, producer, or history helpers directly.
- Tests use an isolated project with a separate source package catalog. They invoke the real executable command and then reason about externally observable results.
- A good test asserts:
  * the emitted response object, not response fields the contract does not provide;
  * the command exit code;
  * the externally observable authoritative state file,
  * the externally observable history event;
  * and, for authoring cases, the validation JSON contract.
- Workflow validation tests are black-box CLI executions reporting the two-state response and validation error paths.
- Task routing tests verify the selected route through the work order and state, not by asserting a particular internal route function was called.
- Producer tests inspect only the state and route history that are externally observable. They do not assert internal function calls or monkey-patch package execution.
- The workflow acceptance fixture remains under test assets and exercises:
  * Boolean and exact-string start input comparisons;
  * a condition fact generated by a workflow script;
  * producer metadata recalculation on a backedge;
  * the dynamic three-backedge limit and fourth-attempt error;
  * exact candidate-arbitration outcomes;
  * static validation acceptance and rejection paths;
  * and state preservation after route evaluation errors.
- Prior art for these tests is the existing set of black-box process-level tests around task admission, CLI validation, source-backed package resolution, human decision commands, closed-world graph validation, and user-facing contract documents.
- Built-in workflow migration is tested through the same CLI seam. A built-in workflow should remain loadable, advance through its ordinary stage gates, and preserve existing user-facing status semantics.
- Old v1 active state is tested through the CLI error contract, without asserting an internal parser exception.
- Runner and creator skill behavior is contract-tested as user-facing input. The runner remains manual-protocol thin, documents `--var` and route evaluation only as far as a runtime agent can understand responses, and retains no business graph. The creator documents explicit invocation, project-local default, user-level-only explicit option, built-in write rejection, and validation integration.
- Skill tests do not attempt to simulate a full AI conversation. They assert that the skill contracts contain the mandatory operational rules and do not reintroduce forbidden legacy commands or auto-trigger language for the creator.
- Runtime state files may be read in tests to validate authoritative results. Tests do not modify runtime state directly, because such manipulation would invalidate the control-plane contract under test.

## Out of Scope

- Aix-style phase-level `when` skip-cascade where a phase exists but is silently skipped by global precondition semantics.
- Parallel fan-out, worker dispatch, barriers, multi-agent scheduling, or developing-condition evaluation in the same release.
- Generic `success`, `failed`, or `max-exhausted` outcome routing.
- Automatic generation of recovery routes after gate failure or after workflow validation failure.
- Self-loop retry semantics.
- A general expression language supporting operators other than equality.
- A general type system, config-driven enum registry, or semantic string normalization.
- A global mutable-variable registry or an agent-editable runtime-variable command.
- Producer output as command-gate repair reasons, workflow instructions, or model-facing explanations.
- Rich evidence capture, arbitrary stdout retention, or an evidence pool for condition facts.
- Production LLM, Jev, probabilistic decision-model, remote-service, or web lookup producers.
- Full production migration of the PRD-to-Spec business flow with Dima, Yuque, DingTalk, multi-Bot gates, or coding-work-item creation.
- Parallel implementation of the existing PRD-to-Spec stage assets or external platform integration gates.
- A runtime-compatible v1 state or workflow parser.
- A v1-to-v2 data migration engine.
- A workflow-authoring UI, web dashboard, task selector, or command for editing active state.
- A status or route-history query command.
- A `wf set`, `wf var`, `wf route`, or equivalent public command for writing variables and route facts.
- Per-producer timeout configuration, per-edge backedge-limit configuration, or an operator command to rewrite route counters.
- Built-in workflow packages accepting direct edits from the workflow creator.
- Reintroducing the v1 global transition list as a parser fallback.

## Further Notes

- The first release goal is routing correctness, not workflow-engine generality. Conditional routing should preserve current site-agent blind progress and deterministic gates rather than approach a general-purpose orchestration platform.
- The design uses dynamic inventory for backedge detection, so a graph remains meaningful under branch and recovery loops without relying on hidden execution-ordered global variables.
- The test fixture's PRD-to-Spec analogy should not be mistaken for the real business migration. A later production migration can reuse the same route primitives while introducing real gates, human decisions, and full process guides.
- The v2 release intentionally reuses the narrow human-confirmation model and other stage constraints since review boundaries must remain independent of route selection. A route choice cannot start until a stage’s human-eyed review evidence has been accepted and fingerprinted through normal flow.
- Any later decision-model producer must remain completely separate from the coding agent that executes a stage and must preserve through its own control-plane audit the exact scalar, decision source, confidence baseline, and route chosen. This release only reserves the producer-extension shape and does not make a probabilistic judgment part of the workflow graph.
