# 11 — Refactor the workflow model seams

**What to build:** the workflow engine should separate its domain model from CLI, persistence, and gate execution, so that changes to state/snapshot handling, workflow interpretation, or CLI output do not all force edits to the same orchestration path.

**Blocked by:** 06 — Enforce inline guide and allow optional gates, 07 — Prevent non-terminal self-loop terminal success, 08 — Standardize the failed JSON contract, 09 — Cover repeated `next` on unchanged non-terminal work

**Status:** ready-for-agent

- [ ] Workflow interpretation is represented by explicit domain concepts rather than nested raw dictionaries
- [ ] Workflow validation, state recovery, gate execution, and CLI orchestration are separated at meaningful seams
- [ ] The public CLI behaviour is preserved
- [ ] The workflow examples still load through the CLI
- [ ] The existing test suite remains external-seam based
