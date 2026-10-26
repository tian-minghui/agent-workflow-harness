# 02 — Add `wf approve --next`

**What to build:** A user can pass `wf approve --next` to submit a human decision and immediately attempt the normal next transition in one command. The command must:

1. Record the human decision exactly as `wf approve` does
2. If accepted, invoke the existing next-transition rules
3. Return the resulting `active`, `blocked`, or `done` response

The default `wf approve` must remain record-only and must not advance the task.

**Blocked by:** 01 — Task envelope on command responses

**Status:** ready-for-agent

- [ ] Default `wf approve` remains record-only
- [ ] Default `wf approve` does not advance the task
- [ ] Default `wf approve` still returns `blocked`
- [ ] `wf approve --next` is accepted as an explicit opt-in
- [ ] If the stage's evidence is valid, `wf approve --next` advances once
- [ ] If the stage has a failing automatic gate, `wf approve --next` remains `blocked`
- [ ] If the decision is rejected, no next transition occurs
- [ ] No existing gate, route condition, or workflow definition is bypassed
- [ ] The `--next` response uses the same five-status contract and enriched task envelope
- [ ] `wf approve --next` preserves the existing human decision and success records in history
- [ ] No new status is introduced
- [ ] `wf reject` remains unchanged and does not gain `--next`
- [ ] Black-box tests cover approve, approve --next, rejection, and blocked/advanced cases
