# Route evaluation happens after human gates

`wf next` completes the active step’s exit gates before evaluating any conditional route. Automatic gates and the active human gate, if declared, must all pass before the control plane runs step-local fact producers, resolves their underlying facts, or arbitrates candidate edges.

A pending or rejected human gate therefore blocks before route evaluation, and approve remains a record-only command. `wf approve` records the decision and refresh-related response; it does not execute condition producers or advance the workflow. On the following `wf next`, the CLI rechecks automatic gates and verifies human evidence freshness before running the step-local fact producer and choosing one outgoing edge.

If a fact producer fails after a valid human approval, the command returns an error without advancing the step. The approval remains attached to the unchanged human evidence and can authorize the next evaluation once the producer issue is fixed. This preserves the existing human-gate semantics while keeping route selection a post-approval control-plane decision.
