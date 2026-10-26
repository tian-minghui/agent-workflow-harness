Status: ready-for-agent

# V1.2 — human confirmation gates

## Problem Statement

The workflow harness can already control a linear workflow with automatic gates, but it cannot represent a step that must be closed by a human decision. Agents can therefore generate an artifact, pass every automatic gate, and move to the next stage even when the business meaning of that artifact still needs human judgment.

The user needs a deterministic, auditable way to insert human confirmation into a linear workflow without teaching the agent a new state, borrowing human attention before automatic gates are ready, or allowing a stale approval to authorize later evidence.

## Solution

V1.2 adds a first-class human confirmation gate to the existing linear state machine.

A human confirmation gate is an ordinary step-exit gate that runs last, after every automatic gate has passed. The gate declares an explicit human request and the list of evidence files that a human decision is bound to. A new `wf next` call reaches the gate only when the step is fully ready for human review. The reviewer then approves or rejects that evidence with dedicated commands. These commands only append a control-plane decision record and never advance the step. Progression remains exclusive to `wf next`.

The agent-facing surface stays minimal and unchanged: a pending human gate is just another blocked state. The status set stays `active`, `blocked`, `done`, `conflict`, and `error`, and the entire human context — business request, evidence paths, and decision actions — is expressed through a stable, single-line `check.reason`. Audit metadata, including the human gate, human decision, and evidence fingerprint, lives only in the control-plane history.

## User Stories

1. As a workflow author, I want a `human` gate type, so that I can insert a required human confirmation into any non-terminal step.
2. As a workflow author, I want the human gate to express a concrete business request, so that the reviewer knows which judgment they are being asked to make.
3. As a workflow author, I want to bind that request to explicit evidence paths, so that the control plane records which artifacts the approval covers.
4. As a workflow author, I want validation to reject a human gate without `request` or `evidence`, so that an ambiguous “please confirm” gate cannot enter the workflow.
5. As a workflow author, I want the evidence set to be small and stable, so that human attention is spent on the right artifacts rather than an unbounded list.
6. As a workflow author, I want the human gate to run last in a step, so that reviewers are only shown evidence that automatic gates have already approved.
7. As a workflow author, I want one human gate per non-terminal step, so that the reviewer does not have to choose which pending decision they are answering.
8. As a workflow author, I want to leave all non-human gates as they are, so that existing workflows continue to work without unrelated redesign.
9. As a workflow author, I want the built-in frontend delivery flow to include human gates only at requirements, design, and PR creation, so that mechanical phases stay cheap and only judgment-heavy phases ask for attention.
10. As a coding agent, I want a pending human gate to return `blocked`, so that I keep the same restart / next / done / conflict / error protocol I already understand.
11. As a coding agent, I want the blocked response to keep only the current stage instruction, so that I do not see future steps or the rest of the workflow.
12. As a coding agent, I want `check.reason` to explain the human request, the evidence paths, and the decision commands, so that I know exactly what to surface to the reviewer.
13. As a coding agent, I want a stable reason prefix, such as `HUMAN_REVIEW_PENDING`, so that I can recognize that this is a human confirmation block without parsing a structured new field.
14. As a coding agent, I want a recurring, stable reason template for pending, rejected, stale, and unchanged states, so that I can respond consistently rather than interpreting prose.
15. As a coding agent, I want the review request to be separate from rejection feedback, so that I can distinguish “waiting for a human” from “the human rejected this evidence”.
16. As a coding agent, I want a rejected gate to remain sticky until a newer human decision replaces it, so that I do not forget what the reviewer objected to after a superficial edit.
17. As a coding agent, I want to see evidence paths in declaration order, so that I can help the human review them in the same order every time.
18. As a human reviewer, I want approve and reject commands that only record my decision, so that I can conclude my review without giving the agent a hidden advance command.
19. As a human reviewer, I want approval to be accepted only after automatic gates pass, so that I am asked to decide on evidence that is already ready for review.
20. As a human reviewer, I want a rejection reason to be mandatory, so that the agent receives actionable feedback rather than an unexplained “no”.
21. As a human reviewer, I want the evidence to be bound to the exact bytes I approved, so that the next stage cannot be run against a different version of the same artifact.
22. As a human reviewer, I want any evidence change after approval to make the approval stale, so that I always re-review the exact version to be advanced.
23. As a human reviewer, I want to be able to approve again after an evidence change, so that my review can track real repairs rather than being trapped by the first rejection.
24. As a human reviewer, I want a new review to be requestable only after the evidence actually changed, so that I am not asked to approve an unchanged rejected artifact.
25. As a human reviewer, I want a reject reason to stay visible until a later human decision supersedes it, so that the agent retains my actual business objection.
26. As a human reviewer, I want the decision to bind the aggregate evidence rather than individual files, so that a combined business judgment is not falsely split across separate approvals.
27. As a human reviewer, I want the workflow to avoid changing formatting or whitespace-only content before reporting another review request, so that every re-review corresponds to a genuinely new evidence version.
28. As a human reviewer, I want a human review request to be rendered as a single-line reason, so that I can read it quickly in the current CLI output.
29. As a human reviewer, I want approve and reject to return `blocked`, so that the workflow does not unexpectedly advance because I answered a gate.
30. As a human reviewer, I want to be able to add an optional approval note, so that I can preserve context without forcing an unnecessary business motivation.
31. As a human reviewer, I want rejection to require a reason, so that my objection is recorded as the actionable repair instruction.
32. As an operator, I want human decision records in the task history, so that I can audit who blocked or approved a stage by control-plane event.
33. As an operator, I want each successful transition to reference the human gate, decision, and evidence fingerprint it relied on, so that I can trace exactly which human review authorized the stage move.
34. As an operator, I want these transitions to be append-only, so that human decisions remain inspectable even after the workflow later moves to another stage.
35. As an operator, I want the human gate to have no impact on unrelated task search, pause, or history behavior, so that this feature is localized to the linear workflow gate.
36. As an operator, I want a deterministic `blocked` response for pending review, so that the existing workflow skill and tests can be adapted without a new schema.
37. As an operator, I want v1.2 to preserve the current five-status contract, so that downstream consumers do not need to add a sixth state to handle human review.
38. As a developer, I want the human decision state to be serialized in the control plane, so that a reviewer can restart the agent or CLI without the pending decision being hidden in process state.
39. As a developer, I want the human gate to be a single, fully declarative YAML construct, so that I do not have to add hidden configuration to gate code.
40. As a maintainer, I want a small, auditable feature that does not introduce a service, identity provider, or UI, so that the next release stays consistent with the current local control-plane scope.

## Implementation Decisions

- Add `type: human` as a new gate type alongside the existing automatic gate types.
- A human gate represents a step-exit condition, not a separate waiting stage.
- Each non-terminal step may contain at most one human gate.
- A workflow that declares more than one human gate in a step is invalid.
- Automatic gates remain unchanged and are evaluated first; the human gate is evaluated last regardless of its YAML position.
- A human gate cannot pass until every automatic gate in that step has passed.
- `wf approve` and `wf reject` are decision-recording commands, not transition commands.
- `wf next` remains the only command that can evaluate a gate and advance the workflow.
- Each human decision is bound to a single explicit `request` and a nonempty list of `evidence` paths.
- A human gate whose `request` is missing or empty is invalid.
- A human gate whose `evidence` list is missing, empty, or uses unsafe or duplicate paths is invalid.
- The workflow validation rejects absolute paths, path traversal, duplicate evidence paths, oversized request strings, and invalid human gates before a task is started.
- Evidence paths remain project-relative and are ordered as declared.
- A pending human reason lists every evidence path completely; it does not summarize the remainder as “etc.” or “+N files”.
- A human decision stores an aggregate, byte-exact fingerprint of all declared evidence.
- The fingerprint is not normalized for whitespace, formatting, or semantics.
- Any byte change in any evidence path makes the prior decision stale for the current step.
- The control plane does not decide whether a cosmetic change was semantically meaningful.
- If the evidence changes after approval, the human gate returns stale.
- If the evidence changes after rejection, the prior rejection is considered resolved-as-input, but the new evidence still requires a fresh approval.
- A new review request is permitted only after a rejected step’s evidence has changed.
- A rejection reason remains visible as part of the blocked response until a newer approval or rejection supersedes it.
- `wf approve` accepts an optional note that is stored in history; it is not required.
- `wf reject` requires a mandatory reason that becomes the actionable repair instruction.
- Approve and reject do not bind a trusted reviewer identity.
- A shell account, locally supplied username, or manually entered reviewer is not treated as identity evidence.
- Any reviewer context supplied by a human is only advisory notes.
- Approval is only accepted when the active workflow and step are reachable and every automatic gate on that step passes.
- Approve and reject return the same five-status contract and never silently advance.
- Pending human review returns `blocked`, not a new status.
- The reason uses fixed, stable English prefixes:
  - `HUMAN_REVIEW_PENDING`
  - `HUMAN_REVIEW_RECORDED`
  - `HUMAN_REVIEW_REJECTED`
  - `HUMAN_APPROVAL_STALE`
  - `HUMAN_REVIEW_UNCHANGED`
- The reason uses a fixed, single-line, deterministic template.
- The reason includes the request, all evidence paths in declaration order, and the concrete approve/reject commands.
- The reason does not include a structured `review` object.
- The reason does not expose the full workflow, future steps, or unrelated gates.
- Human decision and transition metadata is added only to the task history log.
- A successful transition event includes the human gate, the decision, and the evidence fingerprint that enabled it.
- Historical human decisions remain append-only and are never reused by later stages.
- The control plane does not add a dedicated status or history query command in v1.2.
- The built-in frontend delivery workflow adds human gates at three business-review boundaries:
  - after requirements,
  - after design,
  - before PR creation.
- Other frontend stages continue to use automatic gates only by default.
- No workflow gains an unconditional human gate; the gate always comes from explicit workflow YAML.
- A human gate is local audit evidence, not a trusted proof that the person named in an approval note is the reviewer.
- A later trusted approval service can extend this model without changing the command shape or the five-status response contract.

Schema example from the working design:

```yaml
- id: requirements_confirmed_by_user
  type: human
  request: |-
    请确认当前目标、业务边界和验收标准是否符合你的真实预期。
  evidence:
    - docs/requirements.md
```

## Testing Decisions

- The primary testing seam remains the process-level CLI boundary.
- Tests should invoke commands as subprocesses, parse the stable JSON response, and reason about the workflow state only through externally observable artifacts.
- Good tests focus on external behavior, not on the internal helper classes or private storage code.
- The suite should use isolated control-plane homes and temporary projects so human-decision tests never touch real user state.
- Existing black-box workflow and response-contract tests are the prior art for these new tests.
- Validation tests should cover:
  - missing `request`,
  - missing or empty `evidence`,
  - absolute or traversing evidence paths,
  - duplicate evidence paths,
  - more than one human gate in a step,
  - an invalid human gate without requiring runtime information about the current step.
- Gate-order tests should confirm:
  - automatic gates execute before the human gate,
  - human approval blocks when an automatic gate is still failing.
- Response tests should confirm:
  - pending, rejected, stale, and unchanged states return `blocked`,
  - the reason uses the stable English prefix,
  - the reason includes request and every evidence path,
  - the response does not contain a structured review object or a new status.
- Command tests should confirm:
  - approve and reject are record-only,
  - approve does not advance the step,
  - reject does not advance the step,
  - success and errors all use the existing five-status contract.
- Evidence tests should confirm:
  - approval becomes stale after any byte change,
  - rejection is only cleared by a new approval or later rejection,
  - a new review cannot be created with unchanged rejected evidence,
  - rejection feedback persists across evidence edits until a newer human decision.
- Audit tests should confirm:
  - history records the human decision and evidence fingerprint,
  - a successful transition references the human gate, decision, and fingerprint,
  - historical decisions are not reused in later stages.
- Workflow tests should confirm the built-in frontend flow has exactly three human gates at the agreed review points and no unrelated behavioral breakage in the current linear flow.

## Out of Scope

- Adding a sixth response status.
- Adding a workflow authoring UI or terminal wizard.
- Adding a branch, loop, parallel path, or multi-stage alternative route.
- Adding a status or history query command.
- Binding a trusted reviewer identity.
- Integrating a real identity provider.
- Adding a service, MCP server, or external approval UI.
- Implementing a semantic-diff gate that guesses whether formatting-only changes are meaningful.
- Creating a centralized human-review approval platform.
- Tracking per-file approval or partial freshness for multi-file evidence.
- Making approval reusable across stages.

## Further Notes

- Human review is an **audit-grade gate**, not a proof of human intent.
- The deterministic control plane governs progression; human intent is captured in the decision record and implementation history.
- The built-in frontend-delivery workflow can be used as the reference implementation, but the gate model must remain fully declarative and project-agnostic.
- The gate’s request and evidence must be visible in the reason string; none of these fields are allowed to leak into a new structured model-facing field.
