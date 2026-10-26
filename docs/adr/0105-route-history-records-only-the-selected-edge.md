# Route history records only the selected edge

A successful route-selection audit event records the selected source and target step. If the selected edge was conditional, it also records that edge’s condition variable, resolved scalar value, and resolution source. If the selected edge was the default, it records that route kind instead of inventing a condition. Backedges additionally record their per-transition count.

The event does not enumerate unselected candidate edges, condition values for losing targets, or a table of all possible destinations. Although history is useful for diagnosis, it is also readable runtime state; making it a projection of the workflow graph would undermine the agent-blind design. The route record therefore explains the transition that occurred, rather than revealing the routes that did not.

Evaluation errors are similarly minimal. They identify the active step and reason, such as unresolved condition, producer failure, multiple matching edges, or an exhausted backedge, without enumerating all candidate targets.
