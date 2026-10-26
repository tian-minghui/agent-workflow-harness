# Task directories contain only authoritative state and history

A task directory under `.workflow-harness/tasks/<task-id>/` is control-plane runtime state, not a business-artifact store. It contains `state.json` and `history.jsonl`; it does not add an evidence directory, scratch directory, or generic artifact pool. Workflow guides decide where stage artifacts are written, and gates continue to reference those project paths directly.
