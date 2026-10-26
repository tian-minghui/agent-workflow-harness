# Human decision commands are record-only

`wf approve` and `wf reject` never advance a step or the workflow. They append the human decision and its evidence fingerprint to the control-plane record and return the five-status CLI response contract. On success they return `blocked` so the active stage remains current; the next evaluation still has to be performed explicitly by `wf next`.
