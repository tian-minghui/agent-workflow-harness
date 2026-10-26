# Workflow scripts are scalar producers; commands are boolean only

A `workflow_script` producer may produce a boolean or an exact string condition value. It must exit zero and print exactly one nonempty, single-line scalar after trimming leading and trailing whitespace. The scalar `true` or `false` is interpreted as boolean; every other scalar is interpreted as an exact string and is not trimmed within the line, lowercased, or semantically normalized. Extra lines, leading or trailing blank content, exit code two or greater, control characters, arbitrary JSON wrapping, or a timeout are evaluation errors.

A `command` producer cannot express a non-boolean value through stdout. It remains boolean-only: exit code zero means true, exit code one means false, and exit code two or greater means evaluation error. Non-boolean command logic must be wrapped in a workflow script so the control-plane record receives one controlled scalar rather than unquantifiable shell output.

This keeps non-boolean routing usable for `entry_mode == confirmed_prd` or a future Jev-style category such as `risk_level == high` without introducing a general shell parser or a type system.
