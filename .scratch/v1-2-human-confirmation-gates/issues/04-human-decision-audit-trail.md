# 04 — Human decision audit trail

What to build: the control plane records every human approval and rejection in the append-only task history and marks each successful transition with the exact human gate, decision, and evidence fingerprint that authorized it. The audit facts stay in `history.jsonl` and are not exposed through a new status or query command.

Blocked by: 03 — Human rejection cycle.

Status: ready-for-agent

- [ ] A successful `wf approve` writes a human decision record to the task history.
- [ ] A successful `wf reject` writes a human decision record to the task history and includes its reason.
- [ ] Each human decision record includes the associated gate, decision, and aggregate evidence fingerprint.
- [ ] An approval note, when present, is recorded but is not treated as identity evidence.
- [ ] A successful transition event includes the human gate, human decision, and evidence fingerprint that enabled the transition.
- [ ] Human decisions are never reused by a later stage.
- [ ] The same human gate’s decision is not authoritative after the step has advanced.
- [ ] No dedicated `wf status` or `wf history` command is added.
- [ ] The audit trail remains append-only and inspectable through the existing history file.
- [ ] Tests verify the history record at the same external CLI/storage seam as the existing workflow tests.
