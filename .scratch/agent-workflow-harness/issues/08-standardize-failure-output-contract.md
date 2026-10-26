# 08 — Standardize the failed JSON contract

**What to build:** every failing CLI response must use the same stable JSON shape, including initialization failures. The response must identify the workflow step, the gate, and a concise reason, and must never emit a guide.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] All failed responses use a consistent `result: failed` JSON object
- [ ] Gate failures include the current step, the gate id, and the reason
- [ ] Initialization failures fill the same contract, using explicit values where no current step or gate exists
- [ ] No failed response emits the `guide` field
- [ ] The failure contract is covered by black-box CLI tests
