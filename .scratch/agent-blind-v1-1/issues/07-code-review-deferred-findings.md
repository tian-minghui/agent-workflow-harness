# 07 — Code review deferred findings

**What to build:** keep the current implementation and explicitly defer the remaining review findings that are not being fixed in v1.1.

**Blocked by:** None

**Status:** wontfix

- [x] Do not change `runtime.py` to derive resumed `start` state from history instead of `state.json`
- [x] Do not change `gates.py` output truncation from `... + last 1500` to `... + last 1500-...`
- [x] Do not add concurrency safety to project active-task allocation
- [x] Do not add additional tests for response field exclusions across all response statuses
- [x] Do not force absolute file-gate paths to remain relative to the project directory
- [x] Do not change primitive `str` status fields to a dedicated status type
- [x] Do not unify duplicated current-task parsing helpers
