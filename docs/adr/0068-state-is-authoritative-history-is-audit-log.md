# State is authoritative; history is an audit log

V1.2 stores the current runtime state and the variables that control execution in `state.json`. The file is the authoritative source for the active stage, bound source package, workflow fingerprint, and other current execution variables. `history.jsonl` remains append-only and records operational events for audit, but it is no longer the fact source from which runtime state must be reconstructed.

A missing, malformed, or inconsistent `state.json` is an operational error. The harness does not reconstruct state from `history.jsonl`, guess the active stage, or treat the stored snapshot as an alternate authority. `error` is reserved for these unexpected operational and integrity conditions; normal gate failures remain `blocked`.

The authoritative state file uses a minimal closed identity set: `schema`, `task_id`, `workflow_alias`, `title`, `step`, `workflow_dir`, and `workflow_yaml_sha256`. Those fields let the CLI validate the pointer/state relationship, current stage, bound source package, and workflow fingerprint without turning `state.json` into a second history log. Gate results, retry counts, and other transient details are not stored in the authoritative state unless a specific execution feature needs them.

The state file is serialized as human-readable, ordered UTF-8 JSON with `ensure_ascii=False` and stable indentation. Runtime state is written atomically so a partial write cannot silently become the authoritative state. These formatting and durability details are implementation quality decisions, not part of the agent-facing protocol.
