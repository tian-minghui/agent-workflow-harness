# Workflow schema v2 uses only step-local transitions

Conditional routing is defined in workflow schema v2. The document starts with `version: v2`; every non-terminal step owns its complete candidate-edge list under `steps/<name>/transitions`. The schema does not accept the v1 top-level `transitions` list, and it does not mix the two forms.

A v1 workflow is therefore the historical linear single-edge format. The runtime and bundled examples migrate to v2 rather than maintaining dual graph parsers. This one-schema rule avoids hidden precedence between global and step-local edges, keeps validation in one place, and prevents new workflows from acquiring ambiguous duplicate outgoing definitions. The top-level workflow retains only graph-level identity: `entry`, `terminal`, and the complete `steps` mapping.

Schema v2 is a version boundary, not a protocol break: task admission, runtime state, source-package binding, the five status responses, human decisions, gate execution, and agent-blind work-order projection remain unchanged.
