# Human review context stays in the reason string

V1.2 does not add a structured `review` object to the response contract. A pending human gate returns the existing `blocked.check.gate` and `blocked.check.reason`; the reason string includes the human request, the evidence paths to inspect, and the next decision commands. This preserves the minimal five-status, field-stable CLI contract and keeps model-facing parsing simple.
