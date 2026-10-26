# 05 — Explicit backedge and three-cycle limit

**What to build:** support an explicitly declared route target that points to an earlier step, and enforce its three-cycle safety limit from authoritative state rather than reconstruction. This slice ends the loop by returning an error on the fourth attempt and proves that a repaired fact can change the route without breaking the agent-blind response.

**Blocked by:** 04 — Step-local producers and route evaluation transaction.

**Status:** done

- [ ] A transition targeting a step already in the task visited set is recognized as a backedge.
- [ ] A backedge is selected only after an active-step producer successfully resolves the needed condition.
- [ ] Re-entering a step does not bypass its gates or human review gate.
- [ ] The active-step producer reruns before each backedge selection and its current result controls the route.
- [ ] Authoritative state records the visited-step set and a per source-target back-edge count.
- [ ] The same backedge can be selected three times.
- [ ] The fourth attempt returns `error` and leaves the checked step unchecked.
- [ ] The command reason and hint identify the exhausted backedge without revealing alternative edges.
- [ ] Backedge history records only the selected source, target, condition variable, resolved value, source, and current back-edge count.
- [ ] Existing history remains audit-only; modifying history cannot alter the backedge decision.
