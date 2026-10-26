# History records meaningful workflow outcomes

`history.jsonl` is an append-only operational log, not a recovery source. It records the workflow outcomes that materially affect or diagnose a run: `started`, `success`, `blocked`, `error`, `human_decision`, `done`, and `workflow_source_changed`. Ordinary command parsing failures and repeated no-change calls are not logged simply to make the file noisier. The authoritative current state remains in `state.json`.
