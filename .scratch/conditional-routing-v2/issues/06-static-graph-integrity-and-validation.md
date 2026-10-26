# 06 — Static graph integrity and validation

**What to build:** make `wf validate` a full source-backed v2 workflow validator that catches closed-world graph problems before a task is admitted. The slice should make a realistic conditional workflow valid and a malformed graph invalid through the CLI, with no producer or command execution.

**Blocked by:** 01 — Workflow v2 parser and inline validation; 03 — Start inputs and condition-value resolution; 04 — Step-local producers and route evaluation transaction; 05 — Explicit backedge and three-cycle limit.

**Status:** done

- [ ] Every step is reachable from entry.
- [ ] Every non-terminal step has at least one candidate transition.
- [ ] Terminal has no outgoing transitions.
- [ ] Every non-terminal step has a static path to terminal.
- [ ] No transition targets its own source.
- [ ] No source step has duplicate candidate targets.
- [ ] No source step has duplicate `when` predicates.
- [ ] Each step has at most one default candidate.
- [ ] No transition combines `when` and `default`.
- [ ] Every candidate target exists.
- [ ] Producer paths stay inside the workflow package and project arguments stay inside the project.
- [ ] Validation does not execute gates, producers, command scripts, or other side effects.
- [ ] The validator reports bounded, per-problem graph or producer-path errors through the `valid`/`invalid` CLI response.
- [ ] The validator resolves through the same source-backed package precedence used for task admission.
