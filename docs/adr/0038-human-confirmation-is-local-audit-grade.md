# Human confirmation starts as local audit evidence

V1.2 will make human confirmation a first-class workflow gate, but its first implementation will be local audit evidence rather than a strong security boundary. The CLI records the human decision in control-plane history and blocks transitions until that record exists, while acknowledging that a local agent with unrestricted shell access could still invoke the confirmation command. A later trusted approval UI or service can strengthen the boundary without changing the concept of a step-exit gate.
