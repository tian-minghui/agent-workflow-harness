# 03 — Human rejection cycle

What to build: a user can reject a human-gated checkpoint with a mandatory reason. The stage remains blocked, the rejection reason becomes the sticky repair instruction, and the next round would only be accepted after the declared evidence changes.

Blocked by: 02 — Human approval transitions.

Status: ready-for-agent

- [ ] `wf reject --reason` is available as a new command.
- [ ] The command requires a nonempty reason.
- [ ] `wf reject` is record-only and never advances a step.
- [ ] The rejection reason remains visible as part of the active blocked response until a newer human decision replaces it.
- [ ] After a rejection, the same byte-exact evidence cannot be reapproved immediately; `wf next` must remain blocked with a `HUMAN_REVIEW_UNCHANGED` reason.
- [ ] After the evidence changes, `wf next` can report `HUMAN_REVIEW_PENDING` again while still exposing the prior rejection feedback.
- [ ] If the user approves the changed evidence, the stage advances normally.
- [ ] Rejection feedback is preserved across evidence edits until a newer human decision supersedes it.
- [ ] No new status or structured review object is introduced.
- [ ] All behavior is verified through the existing black-box CLI seam.
