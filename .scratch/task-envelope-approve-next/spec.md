# Task envelope and approve-next acceleration

Status: ready-for-agent

## Problem Statement

The workflow harness can create and advance deterministic tasks, but its command responses do not expose enough task context for an agent to resume reliably without contacting the runtime files directly. A successful `wf start` or `wf next` returns the current work order, but does not include the active task ID, current step, or task artifact directory. In an actual run, the agent therefore had to inspect the active-task pointer, read state files, or reverse-engineer the artifact path from a later blocked gate. This creates avoidable friction and makes the CLI response weaker than the state it already owns.

Human review has the same operational gap. A pending human gate is designed on purpose to remain blocked, and `wf approve` must not secretly advance the task. After a successful decision, however, the normal execution pattern still requires a separate `wf next` call before the agent sees the next actual work order. That extra round trip can be useful for audit control, but some agents and operators may prefer an explicit one-command “record this decision and immediately attempt the lawful next transition” action.

## Solution

Keep the existing five-status response contract and all existing fields, and add a stable task envelope to successful task-facing responses. The envelope contains only information the harness already owns authoritatively:

- task ID
- task title
- current step
- task artifact directory

The new fields reduce the need for agents to read runtime files for ordinary context recovery, while keeping runtime state authoritative and immutable. The envelope appears in:

- `wf start`
- `wf next`
- `wf approve`
- `wf reject`

Human decision commands remain record-only by default. Add one opt-in flag:

```bash
wf approve --next
```

When `--next` is supplied, the harness first records the human decision exactly as before. Only if that decision is accepted does it immediately evaluate and select the next lawful transition, returning whatever `wf next` would return for the resulting gate state. This makes the command a closed loop: record, then attempt to continue. Illegal or incomplete evidence still blocks the task, and no command gains the ability to skip gates or shorten a transition.

## User Stories

1. As a coding agent, I want `wf start` to return the active task ID, so that I can keep referencing one concrete task without reading a separate pointer.
2. As a coding agent, I want `wf next` to return the current step name, so that I know which declaration of the workflow owner I am executing.
3. As a coding agent, I want every task response to include the task artifact directory, so that I can address evidence and outputs without reverse-engineering a path from another error.
4. As a coding agent, I want the new fields to be supplemented without removing the old `title` field, so that my existing parsing continues to work.
5. As a coding agent, I want the task envelope to be part of `wf approve` and `wf reject` too, so that I can stay oriented even when a stage remains blocked.
6. As a workflow user, I want `wf approve` to continue only recording my decision by default, so that the existing audit-only contract is unchanged.
7. As a workflow user, I want an opt-in one-step approve command, so that I can avoid a barber-pole of confirm-then-next calls during mechanically simple flow control.
8. As a reviewer, I want `wf approve --next` to validate all automatic gates before my approval is recorded, so that the stage is never advanced from poorly formed evidence.
9. As a reviewer, I want `wf approve --next` to return the actual result of `wf next`, so that I can see the next work order without issuing another command.
10. As a maintainer, I want the returned envelope to stay minimal and stable, so that model agents do not accidentally learn or infer the future workflow graph.
11. As a maintainer, I want all successful and blocked task commands to retain the existing response statuses, so that this improvement does not fork the response contract.
12. As an agent, I want the enriched task object to be backward compatible, so that existing skill scripts can benefit from the new fields without a migration.
13. As an agent, I want the returned step name to correspond to the authoritative active step, not a guessed next step, so that I can safely decide what to do next.
14. As an agent, I want the artifact directory supplied as a project-relative path, so that I can resolve it consistently with the existing command and gate arguments.
15. As a reviewer, I want a failed human decision to remain `blocked`, so that an unapproved instrument cannot cause progression.
16. As a reviewer, I want `--next` to be explicit and opt-in, so that the workflow’s default legal semantics are unchanged.
17. As a workflow author, I want no new schema or business flow property, so that existing v2 workflow packages remain usable without modification.
18. As an operator, I want to be able to use `wf approve` in its current record-only form, so that existing scripts and importers do not break.
19. As an operator, I want `approve --next` to return `active`, `blocked`, or `done` according to the next result, so that the command still feels like part of one state machine.
20. As a maintainer, I want task identity and location to remain owned by the harness, so that the agent cannot invent or synthesize them.
21. As a harness user, I want the same envelope on start, next, approve, and reject, so that I do not need separate data models for the same task.
22. As a harness maintainer, I want task identity and context fields serialized systematically through the CLI, so that tests and skill authors can rely on one shape.
23. As a harness maintainer, I want this improvement to remain within the CLI response and agent-facing protocol, so that internal workflow logic does not need business-specific extensions.
24. As a reviewer, I want the `--next` semantics to be additive, so that human gates remain deterministic and their audit records stay unchanged.

## Implementation Decisions

- Preserve the existing top-level statuses: `active`, `blocked`, `done`, `conflict`, and `error`.
- Preserve all existing response fields.
- Add an enriched `task` object to task-facing responses. It contains:
  - `id`
  - `title`
  - `step`
  - `artifactDir`
- The new `task.id` is the control-plane task ID, not a new independent identifier.
- The new `task.step` is the authoritative current step in state.
- The new `task.artifactDir` is the task artifact directory used by the harness.
- Do not remove the existing `task.title`.
- Do not add a separate `task_id`, `workflow_dir`, `history`, or `run` field.
- Keep the task object minimal; no future routes, visited steps, or workflow package path are exposed.
- Extend task responses in:
  - `wf start`
  - `wf next`
  - `wf approve`
  - `wf reject`
- Preserve the existing `wf approve` semantics by default.
  - It records the decision.
  - It does not advance the stage.
  - It still returns `blocked`.
  - It still instructs the next `wf next`.
- Add one opt-in flag:
  - `--next`
- `wf reject --next` is not added.
- `wf approve --next` performs two ordered steps:
  1. record the human decision exactly as the default command does;
  2. attempt the normal `next` evaluation exactly once.
- If the decision is rejected or the evidence is invalid, no next transition is attempted.
- If the next evaluation is blocked, `wf approve --next` returns that blocked result.
- If the next evaluation succeeds, `wf approve --next` returns the resulting active or terminal state.
- If the next evaluation errors, `wf approve --next` returns the existing error contract.
- The `--next` variant must not bypass any gateway, human gate, or route condition.
- A successful `wf approve --next` response is the normal `wf next` result with the same enriched task envelope.
- No new response status is introduced for `--next`.
- Existing scripts that parse `status`, `task.title`, or `instruction` continue to work.
- Runtime state remains the exclusive authority for progression.
- This feature does not alter task title rules, start input validation, or workflow package authoring.

## Testing Decisions

- The primary testing seam remains the process-level CLI boundary.
- Tests should invoke the real command and parse the emitted JSON response.
- Good tests should assert:
  * the command’s observable exit code;
  * the complete top-level response contract;
  * externally observable state and history files.
- Extend the existing response-contract tests:
  * `wf start` returns `task.id`, `task.title`, `task.step`, and `task.artifactDir`;
  * `wf next` returns the same fields;
  * `wf approve` returns the same fields;
  * `wf reject` returns the same fields.
- Extend human-command tests:
  * default `wf approve` remains record-only and party-shaped;
  * `wf approve` does not advance when no explicit `--next` is supplied;
  * `wf approve --next` advances when gates are valid;
  * `wf approve --next` remains blocked when evidence is incomplete;
  * `wf approve --next` does not advance on a rejected decision;
  * `wf approve --next` does not change existing `wf next` behavior.
- Extend gate-arbitration tests:
  * `--next` evaluates the normal transition logic;
  * the command does not gain an independent route-selection implementation.
- Extend workflow-state tests:
  * active step and artifact directory remain authoritative;
  * approval, rejection, and `--next` still append the existing human decision and success events.
- Extend CLI compatibility tests:
  * old fields remain unchanged;
  * new fields are additive;
  * no implicit six-status contract is introduced.
- Use the existing black-box test suite and subprocess CLI fixtures as prior art.
- Tests should not inspect private runtime classes or reimplementation details.

## Out of Scope

- Changing any task-artifact file.
- Changing human gate or gate evaluation semantics.
- Adding a new status.
- A `wf reject --next` variant.
- Automatic progression from `wf approve` by default.
- Typed or URL-based start input.
- Structured gate diagnostics.
- A new task selector or status command.
- `wf doctor`.
- Any additional workflow package rewrites.
- Changing the workflow authoring format.
- Any prd-to-spec-specific fix.

## Further Notes

This improvement keeps the agent-blind protocol while removing “guess the current task” from successful responses.
The one-step `approve --next` behavior is an opt-in ergonomic addition, not a replacement for the record-only human gate contract.
All authoritative progression remains inside the workflow harness control plane.
