# Human decision parameters stay asymmetric

`wf approve` accepts an optional `--note`, while `wf reject` requires `--reason`. An approval stores optional historical context, but a rejection stores the actionable repair instruction for the next blocked response. The CLI intentionally does not collapse both parameters into `--note`, because the different vocabulary preserves the different consequences of each human decision.
