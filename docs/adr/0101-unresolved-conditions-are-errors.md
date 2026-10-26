# Unresolved conditions are errors

A candidate edge predicate is evaluated only when its condition variable can be resolved. A value of `true` selects that edge, and a value of `false` allows the control plane to consider other candidate edges. A variable that cannot be resolved is neither equivalent to false nor a reason to use the step’s default edge; it is an operational evaluation error.

This distinction preserves the meaning of the default edge. A default is selected only when every conditional predicate for the step was evaluated successfully and none resolved true. It is not a missing-data fallback. Because permissive start inputs can contain names that the active graph does not reference, treating an unresolved variable as false or default could hide a routing typo such as `entry_mod` instead of `entry_mode`.

An unresolved condition returns an `error`, does not advance the step, and records an `unresolved_condition_variable` audit event containing the active step and variable name. Producer failures, malformed output, timeouts, multiple matching edges, and no-default situations use the same error boundary: successful false values and operational evaluation failures never share a status.
