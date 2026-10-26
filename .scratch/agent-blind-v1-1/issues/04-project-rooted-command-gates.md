# 04 — Project-rooted command gates and bounded repair output

**What to build:** command and file gates execute deterministically against the project root from any subdirectory, and failed command gates return a bounded, human-readable output excerpt instead of the gate command or complete logs.

**Blocked by:** 02 — Agent-blind stage traversal

**Status:** ready-for-agent

- [ ] File gates resolve relative paths against the project directory
- [ ] Command gates execute with the project directory as their working directory
- [ ] The same `wf next` result is produced from a project subdirectory and from the project root
- [ ] A failed command gate returns only the current repair order, not the command definition
- [ ] The blocked reason contains the final 1,500 Unicode characters of combined stdout/stderr after cleanup
- [ ] Truncated reasons begin with `...`
- [ ] Empty command output produces the fixed no-output message
