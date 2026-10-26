# 10 — Workflow schema authoring guide

**What to build:** produce a canonical workflow-v2 schema and authoring guide, independent of the creator skill’s orchestration. It should explain, in user-facing language, how to write a valid v2 workflow package from scratch: workflow-level fields, step guides, gates, condition fact producers, candidate edges, defaults, and backedges.

**Blocked by:** 06 — Static graph integrity and validation.

**Status:** done

- [ ] Documents the complete v2 workflow package layout and the role of every authoring field.
- [ ] Explains the source-backed package layout, guide, gates, human gates, step-local fact producers, and candidate transitions.
- [ ] Gives exact syntax for condition variables, Boolean and string literals, `when`, and `default`.
- [ ] Explains producer output protocol, timeout handling, and unresolved versus false conditions.
- [ ] Documents start inputs, resume semantics, and the five execution statuses.
- [ ] Includes one small, end-to-end authoring walkthrough from a business goal to a valid v2 workflow with gates, routes, and one backedge.
- [ ] Includes a copy-ready starter workflow that `wf validate` accepts and that exercises a default route, one conditional route, one step-local producer, and one explicit backedge.
- [ ] Documents the anti-patterns that make a v2 workflow invalid: top-level transitions, self-loops, duplicate candidates, multiple defaults, condition expressions beyond single equality, producer output capture as business data, and default as a substitute for unresolved conditions.
- [ ] Explains why v1 workflows and state are not runtime-compatible or migrated.
- [ ] Explains how to verify a package with `wf validate`.
- [ ] Represents the actual accepted schema, not implementation notes or internal function contracts.
