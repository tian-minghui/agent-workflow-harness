# Conditioned backedges are explicit, not outcome routing

The harness allows a non-terminal step to declare more than one outgoing edge. A backedge is a normal candidate transition that explicitly targets an earlier step. It is selected only after the current step's gates pass and its narrow transition condition evaluates true. A routing gap in the PRD-to-Spec flow, for example, may transition from Spec task assembly back to architecture split only when the workflow declares that backedge and `routing_gap == true`.

Gate failure is not an edge selector. `wf next` continues to return `blocked` for the current step, with the failed gate reason, and does not silently replace that failure with a recovery route. There is also no generic `success`, `failed`, or `maxExhausted` outcome router in the first conditional-routing version. The workflow must declare every route, including recovery routes, as an ordinary edge with a condition and target.

Every selected route records the active step, target step, condition variable, and resolved boolean in control-plane history. This keeps backedges auditable and preserves the agent-blind contract: the agent receives the selected step's work order, never a menu of future or alternative paths.
