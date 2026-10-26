# Runtime state files are readable but not agent-writable

The project-local `.workflow-harness/` files are visible runtime state, not normal project deliverables. An agent may read `task.json`, `state.json`, and `history.jsonl` for preflight or diagnosis, but may not edit them. The workflow CLI remains the single writer; `wf next` is the only command that advances runtime state, and `task.json` is repaired or updated only by the control plane.
