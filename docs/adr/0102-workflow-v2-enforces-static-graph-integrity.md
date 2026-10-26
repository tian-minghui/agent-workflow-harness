# Workflow v2 enforces static graph integrity

Workflow v2 validation treats a workflow package as a complete closed-world graph, not just a set of locally well-formed step objects. Every step must be reachable from `entry`; every non-terminal step must declare at least one outgoing candidate edge; terminal must declare none; and every non-terminal step must have a static path to terminal regardless of runtime condition values. This rejects unreachable declarations and dead-end branches that could make a seemingly valid run impossible to finish.

A step may not target itself and a source step may not contain duplicate targets. A self-loop is retry semantics rather than reconsideration, and duplicate targets should be normalized into one condition fact. A source step likewise cannot repeat the same `when` predicate, contain more than one default edge, or place `when` and `default` on the same transition.

These are static checks in `wf validate` and validation at runtime loading. They do not evaluate conditions, execute gates, or run condition producers.
