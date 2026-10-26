# 03 — Start inputs and condition-value resolution

**What to build:** make conditional routing work for a single `when` edge using only start input, an environment alias, or an existing runtime fact. This slice makes the first real conditional route selectable from control-plane-owned values and preserves resume semantics and exact arithmetic between Boolean and token-string comparisons.

**Blocked by:** 02 — V2 runtime skeleton and task state.

**Status:** done

- [ ] `wf start` accepts repeatable `--var name=value` values using lowercase snake-case names and single-token values.
- [ ] Start inputs are permissive: a token-valid input is admitted even when the current graph does not statically reference its name.
- [ ] Start inputs remain immutable raw strings in authoritative state.
- [ ] The same alias and title can resume when inputs are omitted or repeated exactly; adding or changing an input returns `conflict`.
- [ ] Duplicate use of one variable name in one command is an argument `error`.
- [ ] The condition resolver runs after all ordinary gates and the step’s human gate, if any.
- [ ] A bare `true` or `false` comparison resolves by Boolean normalization; any other token compares exactly as a string.
- [ ] Environment resolution uses only the strict uppercase alias derived from a condition-variable name.
- [ ] An unresolved variable returns `error` and never selects the default edge.
- [ ] A successful route records only the selected target and condition value/source in history, not all candidate edges.
