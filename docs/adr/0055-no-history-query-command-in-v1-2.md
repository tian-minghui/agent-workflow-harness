# No history query command in v1.2

V1.2 keeps the command surface at `start`, `next`, `approve`, and `reject`. Human decision and transition audit records are written to the control plane's existing `history.jsonl`; there is no dedicated `wf status` or `wf history` query command. Inspecting the append-only file remains an operator fallback until human gates are stable enough to justify a richer operational interface.
