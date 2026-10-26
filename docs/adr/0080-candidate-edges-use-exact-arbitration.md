# Candidate edges use exact arbitration

When a step has multiple conditional outgoing edges, the control plane evaluates all candidate `when` predicates for that step and permits exactly one to resolve true. Multiple true edges are an `error`, not a first-match win. If none resolves true, the control plane selects the step’s single default edge; no default edge is another `error`. A transition cannot declare both `when` and `default`.

YAML declaration order therefore never gives a transition hidden priority. This makes routing explicit and prevents a minor reorder of edges from changing the route. Workflow validation can also reject a step with more than one default before runtime execution.
