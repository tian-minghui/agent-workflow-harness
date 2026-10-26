# 08 — PRD-to-Spec routing acceptance fixture

**What to build:** build a deterministic acceptance asset under test assets that exercises the routing semantics shared with the real PRD-to-Spec flow. It should prove that the model can express an admission mode split, a conditional technical-contract step, and a routing-gap backedge without using the production PRD catalog.

**Blocked by:** 07 — V2 built-in migration and clean v1 retirement.

**Status:** done

- [ ] The fixture uses a source-backed package that is copied into an isolated project during tests and is not installed as a built-in workflow.
- [ ] Start inputs select one of the two entry-mode branches.
- [ ] A Boolean condition from a step-local producer enables the conditional technical-contract clarification step.
- [ ] A false condition selects the default normal path.
- [ ] A routing-gap producer returns true and selects the explicit backedge to architecture split.
- [ ] Re-entering architecture split allows the routing-gap fact to refresh.
- [ ] A repaired route returns the workflow to the forward candidate path.
- [ ] The 4th attempt of the same backedge returns the authoritative 3-cycle-limit error.
- [ ] The fixture proves producer failure, malformed output, and timeout return `error`, never `false`.
- [ ] The fixture is fully deterministic and requires no network or external platform access.
- [ ] Black-box tests verify all results through `wf validate`, `wf start --var`, and `wf next`.
