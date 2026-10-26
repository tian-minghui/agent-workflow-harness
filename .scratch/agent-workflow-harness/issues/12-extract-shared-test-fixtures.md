# 12 — Extract shared workflow test fixtures

**What to build:** the test suite should share a small workflow fixture builder so every minimal workflow variation does not inline a near-identical YAML document. The tests should stay focused on the CLI contract rather than repetitive YAML text.

**Blocked by:** 11 — Refactor the workflow model seams

**Status:** ready-for-agent

- [ ] Repeated test workflows use a shared fixture builder
- [ ] Tests still exercise behavior through the public CLI boundary only
- [ ] Tests still distinguish successful, failed, terminal, and repeated-unchanged scenarios
- [ ] The full test suite retains the same functional coverage
