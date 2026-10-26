# 02 — Human approval transitions

What to build: a user can record a final human approval on an active human gate. This creates a record in the task history but never advances by itself. The next normal `wf next` call can then pass the human gate and continue the stage. The approval is bound to a byte-exact aggregate fingerprint of the gate’s `evidence`, so changing any evidence before progression makes the approval stale.

Blocked by: 01 — Human gate schema and pending block.

Status: ready-for-agent

- [ ] `wf approve` is available as a new command.
- [ ] `wf approve` is record-only and never advances a step.
- [ ] `wf approve` is only accepted when the active step’s automatic gates all pass and the human gate is the sole remaining blocker.
- [ ] A successful approval stores a decision for the current human gate.
- [ ] The approval records a byte-exact aggregate fingerprint of all declared evidence.
- [ ] If any evidence path changes after the approval, the next evaluation returns `blocked` with a `HUMAN_APPROVAL_STALE` reason.
- [ ] If the evidence is unchanged, the next `wf next` advances the stage.
- [ ] `wf approve --note` is optional; when provided, it is accepted as supplementary human context.
- [ ] The command returns the existing five-status contract and does not add a new status.
- [ ] The test seam is the process-level CLI boundary plus the existing persisted control-plane history file.
