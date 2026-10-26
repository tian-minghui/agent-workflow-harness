# Blocked gate repair response

A failed workflow gate will return a `blocked` status with the active task title, current-stage instruction, failed gate, and concise reason. Blocked is therefore an active-but-cannot-advance state, not a terminal or operational failure. This lets the agent repair the current stage without reading workflow YAML, while never exposing the next stage or workflow graph.
