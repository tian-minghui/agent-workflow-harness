# Start variables use the condition token rule

`wf start --var name=value` accepts only the same narrow token forms that conditional routing can compare. The name is nonempty lowercase snake case. The value is a nonempty token containing ASCII letters, digits, dots, underscores, hyphens, or slashes; the bare tokens `true` and `false` are also valid. Empty values, spaces, quotes, newlines, control characters, and values longer than 256 characters are rejected before a task is created.

This restriction follows the current purpose of start inputs: they conditionally influence routing, not carry free-form business content. Complex text or semantic judgment belongs in a project artifact read by a `workflow_script` producer, which reduces that judgment to a scalar condition value. The restriction prevents a hidden second state store and avoids confusing start input with a business payload.
