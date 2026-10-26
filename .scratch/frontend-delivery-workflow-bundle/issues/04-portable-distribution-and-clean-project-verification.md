# 04 — Portable distribution and clean-project verification

**What to build:** A user can install the distribution once and start the frontend-delivery workflow from any unrelated project directory without needing a source checkout or the harness working tree. The workflow, its resources, and its runtime help are available through the same alias in every supported environment.

**Blocked by:** 03 — Frontend-delivery workflow bundle adoption

**Status:** ready-for-agent

- [ ] The workflow bundle and its resources are included in packaged builds, not only in the source tree
- [ ] The installed distribution can resolve and start the frontend-delivery alias from a clean external environment
- [ ] Alias startup and gate execution do not depend on the repository’s `examples/` directory
- [ ] Build verification proves that workflow definitions, templates, and scripts remain together in the installed output
- [ ] A clean-project smoke run reaches at least the first resource-backed stage in an unrelated working directory
- [ ] Documentation and examples accurately describe the new directory-backed workflow package, while making clear that example files are not runtime dependencies
- [ ] External-directory verification is automated so future workflow packaging changes cannot silently break portability
