# State v2 uses raw inputs and provenance-bearing facts

Workflow state v2 stores start inputs as a flat map from a lowercase snake-case condition-variable name to the exact raw string supplied by `wf start --var`. Inputs are not normalized to booleans when persisted and are not wrapped in a value object. Comparison-time normalization remains confined to the narrow `when` predicate, preserving the original caller intent for audit.

Runtime facts are stored as a map from condition-variable name to a provenance-bearing record. The record contains the current scalar `value`, the `producing_step`, `producer_type`, and `producer_ref`. A `workflow_script` produces a JSON boolean for bare `true` or `false`; every other valid scalar is an exact string. A `command` can produce only a boolean value. Fact records do not store timestamps, command stdout, evidence fingerprints, or environment values.

Environment lookup is not persisted in either map. If an environment alias participates in a route decision, history records that route selection with the logical variable and resolved value, but no ambient process value is converted into task state. This keeps machine-local overrides visible in audit while ensuring that they cannot silently become durable task evidence.
