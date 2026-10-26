# History record timestamps and readable serialization

## Status
Accepted

## Context
The append-only history log records audit events; runtime state is authoritative in `state.json` (see ADR 0068). Early v1.1 records omitted event times, and `Task.write_state` / `Task.append_history` used Python's default JSON escaping, which made Chinese text appear as `\uXXXX` in control-plane files.

## Decision
Every newly appended history event includes an event-local UTC ISO-8601 `timestamp`. Control-plane JSON artifacts are persisted as UTF-8 with `ensure_ascii=False` so files remain directly inspectable in a terminal.

## Consequences
New audit records can be ordered and correlated with external logs. Existing history events did not record times, so they are not backfilled or invented; legacy records retain only the facts that were recorded when they happened. State remains a minimal current-stage projection and therefore does not need a separate timestamp.
