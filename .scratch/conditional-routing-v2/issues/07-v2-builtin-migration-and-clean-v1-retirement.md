# 07 — V2 built-in migration and clean v1 retirement

**What to build:** migrate the built-in workflows to v2 and retire the superseded v1 runtime surface as a clean version boundary. The slice should leave a fully working, v2-only control plane that still preserves the external response contract and existing stage behavior.

**Blocked by:** 06 — Static graph integrity and validation.

**Status:** done

- [ ] Built-in workflow packages use v2 step-local transitions exclusively.
- [ ] The runtime path uses the v2 graph and task-state schema only.
- [ ] The superseded top-level transition form is rejected by validation and by runtime loading.
- [ ] No hidden v1 parser or state migration path remains in the release.
- [ ] Existing built-in workflow stage behavior remains externally observable and unaffected.
- [ ] Existing workflow guide references still resolve through the source-backed package path.
- [ ] Old v1 task state returns a clear `error` with the established v2 restart hint.
- [ ] The full regression suite runs through the CLI black-box seam and remains green without relying on old-format fixtures.
