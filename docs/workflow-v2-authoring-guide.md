# Workflow v2 Authoring Guide

Workflow-v2 is the only accepted authoring model for new workflow packages. A package is a source-backed directory that you can validate in place, start as a project task, and reason about without exposing the full graph to the executing agent.

This guide explains how to author a complete workflow-v2 package from scratch.

## Package layout

A workflow package is a directory that must contain a `workflow.yaml` file:

```
<alias>/
  workflow.yaml                 # required
  references/                    # optional markdown
  scripts/                       # optional Python gate scripts
  resources/                     # optional shared templates or reports
  assets/                        # optional static files
  templates/                     # optional output templates
```

The harness does not copy or snapshot the package. It resolves the source package by alias and binds the active task to the package’s absolute path and the SHA-256 fingerprint of `workflow.yaml`.
A running task checks only `workflow.yaml` for source drift; other files in the package may change while the task is still active.

The lookup precedence for aliases is:

1. `<project>/.agents/workflows/<alias>/`
2. `~/.agents/workflows/<alias>/`
3. `agent_workflow_harness/workflows/<alias>/`

Only `workflow.yaml` is mandatory. Other folders are optional packaging material and are never used unless the workflow explicitly references them with template variables such as `${workflowDir}`.

## Task artifacts and template variables

Every task gets a project-local artifact directory before the first work order is returned:

```text
<project>/.workflow-harness/task-artifacts/<title-slug>-<task-id>/
```

The title must be a natural English line of 5–120 characters containing only ASCII letters, digits, spaces, and hyphens. It is not a directory-name format such as `implement-user-profile-export`; the control plane creates the lowercase, bounded slug. The complete task ID suffix guarantees that identical titles never share artifacts.

Model-produced business artifacts, including requirements, specs, reports, and review notes, should use concrete paths under `${taskDir}`. Source code, tests, and configuration remain in their normal project locations. The harness does not force every file gate or human-evidence path to live under `${taskDir}`, because project findings can also be legitimate evidence.

Template variables use one strict grammar:

```text
${workflowDir}
${taskDir}
${lowercase_start_input_name}
```

Valid sources are only:

1. the absolute source-package directory, `${workflowDir}`;
2. the project-relative task artifact directory, `${taskDir}`;
3. immutable start inputs admitted by `awh start --var`.

Template resolution is an exact, single-pass replacement. It never reads environment variables, runtime route facts, or history; performs no nested expansion; and has no escape mechanism. `awh validate` checks placeholder syntax. `awh start` resolves every template against the submitted inputs and returns `error` before creating a task if a referenced input is missing.

Template variables may appear in stage guides, `file_exists` paths, command-gate commands, human-gate requests, human evidence paths, `workflow_script` project arguments, condition-producer commands, and condition-producer project arguments.

## Workflow schema

A workflow-v2 package must start with `version: v2`. The top-level `transitions:` list from schema v1 is **not** accepted.

```yaml
version: v2
entry: draft
terminal: done
producer_timeout_seconds: 30

steps:
  draft:
    title: Draft
    guide: Draft the work contract.
    gates: []
    condition_producers: {}
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
```

### Top-level fields

| Field | Requirement | Meaning |
|---|---|---|
| `version` | required | Must be `v2`. |
| `entry` | required | The step the objective starts from. |
| `terminal` | required | The step the objective must be able to reach. |
| `steps` | required | Mapping of step names to step objects. |
| `producer_timeout_seconds` | optional | Bounded timeout shared by every condition producer. Default is `30`. Allowed range is `1` to `300`. |

The entry and terminal steps must be different. Every step in the package must be statically reachable from `entry`, and every step must have a static path to `terminal`.

### Step fields

Each key under `steps` is a step name. Step names can be plain YAML strings, including Chinese names; they do not affect routing behavior.

```yaml
draft:
  title: Draft
  guide: Draft the current objective.
  gates:
    - id: draft_file
      type: file_exists
      path: docs/draft.md
  condition_producers:
    additional_review:
      type: command
      command: "grep -q 'extra review' docs/draft.md"
  transitions:
    - to: done
      default: true
```

| Field | Requirement | Meaning |
|---|---|---|
| `title` | optional | Human-readable description. The runtime does not use `title`. |
| `guide` | required for non-terminal steps | One-paragraph instruction for the current stage. The guide may use template variables (`${workflowDir}`, `${taskDir}`, or start inputs). |
| `gates` | optional | List of automatic gates. |
| `condition_producers` | optional | Step-local producers used by this step’s conditional routes. |
| `transitions` | required for non-terminal steps | The list of outgoing candidate routes. Only the terminal step may omit it. |

Terminal steps are normally declared with `guide: null` because there is no next instruction to give.

## Gate types

Automatic gates are evaluated in the order they are declared, fail fast, and return the first failing gate.

### `file_exists`

```yaml
gates:
  - id: spec_file
    type: file_exists
    path: docs/spec.md
```

`file_exists` gates resolve `path` relative to the target project directory.

### `command`

```yaml
gates:
  - id: test_command
    type: command
    command: "python3 -m unittest discover -v"
```

`command` gates run with the target project directory as the current working directory. They may use template variables to reference package files, task artifacts, or start inputs.

A failing command returns only a bounded excerpt of stdout/stderr, never the command definition itself.

### `workflow_script`

```yaml
gates:
  - id: contract_gate
    type: workflow_script
    script: scripts/needs_contract.py
    project_args:
      - ${taskDir}/contract.md
```

`workflow_script` gates execute a Python file stored inside the workflow package. `script` must stay package-relative and end in `.py`. Entries in `project_args` must stay project-relative. The script’s exit code determines whether the gate passes.

### `human`

```yaml
gates:
  - id: user_confirmation
    type: human
    request: Please confirm that the proposal is correct.
    evidence:
      - docs/contract.md
```

A `human` gate is a step-exit gate that requires a recorded decision. It is evaluated after all automatic gates have passed. A step may declare at most one human gate. The request and every evidence path may use template variables. Evidence paths resolve relative to the target project directory.

Human gates:

- require a nonempty `request`
- require a nonempty, duplicate-free list of at most `5` evidence paths
- run only after every automatic gate on the same step passes
- return a single-line `HUMAN_REVIEW_*` reason with the request, evidence, and decision commands
- are record-only: `awh approve` and `awh reject` do not advance the workflow

Terminal steps cannot contain `human` gates.

## Condition grammar and producers

Workflow v2 supports only one condition form:

```yaml
when: <condition_variable> == <literal>
```

### Variables and literals

- `condition_variable` must be lowercase snake-case: `^[a-z][a-z0-9_]*$`
- Literal values must be a single ASCII token
- `true` and `false` are the only Boolean literals
- Every other token is compared as an exact string

Examples:

```yaml
when: needs_contract == true
when: entry_mode == confirmed_prd
```

The harness does not accept conjunction, disjunction, inequality, regular expressions, spaces, quotes, multiline text, or trailing whitespace around the condition token.

### Step-local producers

`condition_producers` are declared on the step whose outgoing candidate route consumes them:

```yaml
decide:
  condition_producers:
    needs_contract:
      type: workflow_script
      script: scripts/needs_contract.py
      project_args:
        - docs/spec.md
```

Producer rules:

- A conditional variable may have at most one producer in the workflow.
- The producer must belong to the step that actually consumes it.
- `workflow_script` must emit one nonempty, single-line scalar and exit `0`.
- `command` is Boolean-only: `0` means `true`, `1` means `false`, and `2` or greater means an evaluation error.
- `producer_timeout_seconds` is workflow-wide; it applies to every producer in the package, not to a single step or producer.
- A step-local producer beats an existing runtime fact for the same variable.
- Any producer failure, malformed output, timeout, or unresolved variable is an operational `error`, not a valid `false`.
- A command producer may use `${workflowDir}` when it needs to call a package-owned file.
- The resolution order for the same variable is step-local producer, then runtime fact, then start input, then the `WF_<VARIABLE>` alias.

### Conditions versus defaults

```yaml
transitions:
  - to: review
    when: needs_review == true
  - to: done
    default: true
```

Interpretation:

1. Every `when` candidate on the current step is validated.
2. Exactly one candidate may match.
3. If one matches, that candidate is selected.
4. If no candidate matches, the `default` candidate is selected.
5. If no candidate matches and no `default` is declared, the step is an operational `error`.

A step may declare at most one `default` transition, and `default` may not be combined with `when` on the same transition.

## Explicit backedges

A backedge is simply a transition that targets an already-visited step:

```yaml
transitions:
  - to: draft
    when: needs_revisit == true
  - to: done
    default: true
```

Backedges are explicit, not synthesized from gate failures. The harness counts the same source-to-target backedge and allows at most **three** selections. The fourth attempt is an operational `error`.

## Start inputs and resume semantics

Task creation may accept start inputs. `awh start` does **not** evaluate gates; it only creates or resumes the task context and returns the current instruction:

```bash
awh start feature-delivery --task "Implement a small change" --var entry_mode=confirmed_prd
```

Start inputs:

- variable names use lowercase snake_case and can be referenced as `${name}` in template fields
- every referenced template input must be supplied at creation; otherwise `awh start` returns `error` and does not create a task
- variable names use lowercase snake_case
- values are single tokens, at most 256 characters
- one variable may appear once in the same command
- inputs are immutable for the lifetime of the task

If you call `awh start` again with the same alias and title:

- `${}`-style start inputs may be omitted or repeated exactly
- adding a new variable, changing a value, or repeating a different variable returns `conflict`
- the active input set is never mutated

## Response statuses

Workflow execution returns one of five task statuses:

| Status | Meaning |
|---|---|
| `active` | Go execute the returned instruction. |
| `blocked` | The current stage is not yet approved. |
| `done` | The objective is complete. |
| `conflict` | Another task is active. |
| `error` | The task or route evaluation failed. |

`awh start` may return `active` or `conflict`. `awh next` may return `active`, `blocked`, or `done`. An invalid command, invalid state, or evaluation failure returns `error`.

## Copy-ready starter workflow

The repository ships one minimal, end-to-end starter at `examples/workflow-v2-starter/`. It uses one default route, one conditional route, one command producer, and one explicit backedge:

```yaml
version: v2
entry: draft
terminal: done
producer_timeout_seconds: 30

steps:
  draft:
    title: Draft
    guide: Draft a concise requirement note.
    gates:
      - id: draft_file
        type: file_exists
        path: ${taskDir}/draft.md
    transitions:
      - to: review
        default: true

  review:
    title: Review
    guide: Decide whether the draft needs another pass.
    condition_producers:
      needs_revisit:
        type: command
        command: "grep -q 'revisit' ${taskDir}/draft.md"
    transitions:
      - to: draft
        when: needs_revisit == true
      - to: done
        default: true

  done:
    title: Done
    guide: null
```

Copy this package into:

```
<project>/.agents/workflows/starters/<alias>/
```

Then run:

```bash
awh validate <alias>
awh start <alias> --task "Use this workflow package"
```

## Authoring walkthrough

A workflow begins with a business goal that you can reduce to three concrete objects:

1. the **entry** stage, where work starts
2. one or more **gates**, which decide when the stage is ready to leave
3. one or more candidate **routes** to the next stage

For a small example, suppose the business goal is “finish a draft after the user decides whether it needs an extra pass.”

Start by writing two stages:

1. **draft** — create `${taskDir}/draft.md`.
2. **review** — decide whether another pass is needed.

Add a `file_exists` gate to `draft` to ensure work has begun. Add a command producer under `review` to detect a marker in the file. Then declare two candidate routes from `review`: back to `draft` when `needs_revisit == true`, or forward to `done` by default. This gives a real workflow with:

- a default edge
- a conditional edge
- a producer-backed route decision
- an explicit backedge
- a terminal step

To verify it, copy the example directory into a project, run `awh validate <alias>`, and then start it with a simple task title. If validation returns `invalid`, fix the reported reason and validate again.

## Anti-patterns to avoid

Do not use the v1 global transition list. Do not place `transitions` at the top level.

Do not declare the same conditional variable twice. Do not create a self-loop from a step back to the same step. Do not declare duplicate candidate targets. Do not define two default edges from the same step. Do not use a condition expression beyond single equality. Do not treat a default edge as a generic fallback for an unresolved variable.

Do not put a producer on a step that does not reference it. Do not let a `workflow_script` try to capture business data beyond one scalar line. Do not let a `command` producer return arbitrary text.

Do not use a backedge as an implicit retry triggered by a failed gate. Use the default, conditional, or explicit backedge only when it represents a deliberate route decision.

## v1 compatibility

Workflow-v2 and task-state v2 replace the previous formats directly. The harness does not:
- parse workflow-v1 YAML
- accept v1 task state
- automatically migrate v1 workflows
- automatically repair v1 history

If a package or task uses v1, start a replacement v2 task instead of migrating it.

## Verify with `awh validate`

`awh validate <workflow-alias>` is a side-effect-free authoring command.

It checks:
- `version: v2`
- the package graph
- step-local transitions
- condition grammar
- template-variable syntax
- producer declarations
- route and terminal reachability
- static terminal reachability

It does not run gates, execute condition producer scripts, or create a task.

A valid response looks like:

```json
{"status":"valid","alias":"feature-delivery"}
```

An invalid response names one concrete validation reason:

```json
{"status":"invalid","reason":"Workflow validation failed: step draft has a self-loop"}
```

Use `awh validate` before `awh start`. If validation eventually returns `invalid`, the workflow is not finished.
