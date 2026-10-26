# 03 — Ordered multi-gate fail-fast output

**What to build:** a step can contain more than one gate, gates are executed in declared order, the first failure stops evaluation, and the CLI returns a reason-only failure object without a guide or state advance.

**Blocked by:** 01 — Minimal single-step traversal

**Status:** ready-for-agent

- [ ] A step supports an ordered list of gates
- [ ] The first failing gate ends evaluation immediately
- [ ] Failed output includes the current step, failed gate, and concise reason
- [ ] Failed output does not include a step guide
- [ ] State does not advance after a failed gate
- [ ] The failure is recorded in history
- [ ] Command gates and file gates both work
