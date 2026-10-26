# 06 — Enforce inline guide and allow optional gates

**What to build:** the workflow engine must reject any non-terminal step that does not explicitly declare an inline guide. Gates must remain optional throughout the workflow language and be treated as an empty list when omitted.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Initialization fails if a non-terminal step omits its inline guide
- [ ] A non-terminal step with an empty inline guide is rejected
- [ ] A step **without** a `gates` key initializes successfully
- [ ] A step with an explicitly empty `gates` list initializes successfully
- [ ] The terminal step may use an explicit null guide without being rejected
- [ ] Existing example workflows continue to pass initialization
