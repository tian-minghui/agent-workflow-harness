# Fact producers use a strict boolean protocol

Status: Superseded by ADR 0082

A conditional fact producer must make three outcomes distinguishable: the condition is true, the condition is false, or the control plane could not reliably evaluate the condition. A `workflow_script` producer therefore must exit zero and print exactly `true` or `false` after trimming leading and trailing whitespace. A `command` producer maps exit code zero to true and exit code one to false; exit code two or greater is an evaluation error. A timeout, failed process start, or any malformed output is also an evaluation error.

Producer stdout is not a repair reason and is not echoed into the agent-facing response. False is a valid business result for routing, while evaluation failure is an operational `error`. Keeping those outcomes separate prevents a crashed or missing dependency from masquerading as a normal fallback path and gives route-history records an unambiguous truth value.
