# Human-gate pending uses blocked status

V1.2 keeps the five-status response contract when the human gate is pending or rejected. Human review does not introduce a new model-facing status; `wf next` returns `blocked` with the active stage instruction, the human gate id, and an actionable reason such as approval pending, rejection feedback, or stale approval. The status describes whether the control plane may advance, while `check.reason` carries the repair-specific detail.
