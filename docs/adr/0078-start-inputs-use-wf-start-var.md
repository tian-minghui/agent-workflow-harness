# Start inputs use `wf start --var`

Workflow task inputs are supplied through a repeatable `--var name=value` option on `wf start`. This matches the Aix-style user model while preserving the harness boundary: the CLI parses and stores the inputs at task creation, and the transition condition never names their storage source. The condition continues to use the narrow `when: <condition-variable> == <literal>` form.

A variable name is lowercase snake case and a value is initially stored as a string. Boolean-like conditions are normalized when compared against a narrow `when` literal; the original input remains available for audit. The same name cannot be provided twice in one start command. Start inputs are immutable during the active task, and no `wf set var` command is exposed. A matching `wf start` resume returns the existing work order rather than accepting new task inputs.
