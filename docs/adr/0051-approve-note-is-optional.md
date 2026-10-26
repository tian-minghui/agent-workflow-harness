# Approve notes are optional

V1.2 allows `wf approve --note ...` but does not require a note. A plain approval records the decision and evidence fingerprint, while an optional note preserves useful context for audit and later discussion. Rejection remains different: `wf reject --reason ...` is required because the reason is the actionable repair instruction for the agent.
