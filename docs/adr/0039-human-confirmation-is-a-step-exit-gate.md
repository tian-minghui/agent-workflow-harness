# Human confirmation is a step-exit gate

V1.2 models human confirmation as a gate attached to the current step, not as a separate waiting stage. The confirmation command records a decision for the active gate, while `wf next` remains the only command that can evaluate gates and advance the workflow. A rejection keeps the step blocked and exposes the rejection note as the repair instruction.
