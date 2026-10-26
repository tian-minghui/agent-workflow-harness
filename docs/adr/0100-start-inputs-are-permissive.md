# Start inputs are permissive

`wf start --var` does not reject a token-valid input merely because the currently bound workflow has no transition condition referencing that name. Start inputs are admitted as task-scoped arguments and persisted in authoritative state. If no `when` condition uses a name, the value has no routing effect during the active run; it is still preserved for inspection and audit.

This keeps task creation decoupled from one particular graph edition. A caller may pass a stable set of inputs — for example a system ID, deployment mode, or integration option — even when the active workflow or a future schema-compatible workflow does not yet consume every one. The control plane does not claim to know the business meaning of an unused token, and task creation is not turned into a second workflow validator.

The token and resume contracts still apply: names must be lowercase snake_case, values must be nonempty single tokens, duplicate names in one command are errors, and an active task can only be resumed by omitting inputs or repeating the original inputs exactly. An unused input is not a workflow definition error.
