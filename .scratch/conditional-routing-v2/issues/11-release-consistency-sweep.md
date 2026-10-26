# 11 — Release consistency sweep

**What to build:** finish the release with consistent, v2-only user-facing documentation, ADR references, package metadata, and tests. This slice should leave the repository ready for a clean v2 release and no contradiction between the runtime, validator, skills, and guide language.

**Blocked by:** 01 — Workflow v2 parser and inline validation; 02 — V2 runtime skeleton and task state; 03 — Start inputs and condition-value resolution; 04 — Step-local producers and route evaluation transaction; 05 — Explicit backedge and three-cycle limit; 06 — Static graph integrity and validation; 07 — V2 built-in migration and clean v1 retirement; 08 — PRD-to-Spec routing acceptance fixture; 09 — Runner skill v2 contract; 10 — Workflow schema authoring guide; 10b — Workflow creator skill.

**Status:** done

- [ ] User-facing documentation accurately describes only workflow schema v2.
- [ ] User-facing documentation no longer teaches the superseded top-level transition list or v1 runtime compatibility.
- [ ] Documentation describes `wf validate`, `wf start --var`, condition producers, exact arbitration, and backedge limits.
- [ ] ADR indices and referenced decisions match the accepted v2 model.
- [ ] Domain glossary and design guides match the accepted v2 vocabulary.
- [ ] Package metadata includes any new workflow fixtures required by tests without exposing the acceptance fixture as a user workflow.
- [ ] The runner and creator skills are both consistent with the release and neither duplicates the other’s responsibility.
- [ ] No docs use v1 state migration as if it were supported.
- [ ] No docs suggest failure-outcome routing, self-loop retry, parallel fan-out, or generic API-based producer evaluation.
- [ ] The entire black-box regression suite passes through the CLI process seam.
