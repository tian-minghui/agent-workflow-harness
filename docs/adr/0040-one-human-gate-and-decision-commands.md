# One human gate and explicit decision commands

V1.2 validates that a nonterminal step contains at most one `type: human` gate. The minimal decision protocol is `wf approve` for acceptance and `wf reject --reason ...` for rejection, without asking the user to identify the gate. These commands append a control-plane decision record and never advance the workflow; gate evaluation and transition remain exclusive to `wf next`. Rejection requires a concrete reason so the next blocked response can turn it into an actionable repair instruction.
