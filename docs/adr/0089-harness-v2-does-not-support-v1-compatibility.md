# Harness v2 does not support v1 compatibility

Workflow schema v2 and task-state v2 replace the prior v1 formats directly. The harness does not preserve a v1 graph parser, does not accept v1 active task state, does not rewrite old workflows in place, and does not provide an automatic v1-to-v2 state or graph migration.

This is a deliberate clean-version boundary. Conditional routing changes the route model from a global single-edge list to step-local candidate edges with condition-producing facts. Backfilling an old task would require inventing inputs, facts, provenance, and route history that the v1 task never recorded. Treating those synthetic fields as migrated state would create misleading audit evidence rather than a real migration.

An existing v1 active task should surface an operational `error` instead of being resumed or converted. The old task directory remains readable as historical audit material, but a run created with the new harness must use a v2 workflow and state schema. Transitional compatibility is left to git history and migration documentation, not runtime code.
