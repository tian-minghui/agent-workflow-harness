# 01 — Workflow v2 parser and inline validation

**What to build:** create the v2 workflow representation and a side-effect-free CLI validation path that can parse a minimal v2 workflow using step-local candidate edges, without creating or changing a task. The slice should be demoable by pointing `wf validate <alias>` at a minimal v2 package and getting valid/invalid JSON.

**Blocked by:** None — can start immediately.

**Status:** done

- [ ] A v2 workflow definition parses a minimal graph using steps whose non-terminal entries own candidate transitions.
- [ ] A candidate transition names its target and supports either `when` or `default`, never both.
- [ ] The v2 parser rejects a definition containing the superseded top-level transition list.
- [ ] `wf validate <alias>` resolves the source-backed package using the normal alias precedence and outputs only the two-state authoring response.
- [ ] Successful validation reports `valid` with the resolved alias.
- [ ] Failed validation reports `invalid` with bounded, user-actionable syntax errors and no workflow command is created.
- [ ] Validation does not read or write active-task state, history, or source-fingerprint state.
- [ ] End-to-end tests exercise the CLI from an isolated project with a minimal v2 source package.
