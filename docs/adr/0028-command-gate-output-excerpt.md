# Command gate output excerpt

A failed command gate will report a bounded stdout/stderr excerpt as the blocked response reason. The response will not include the gate command itself. The excerpt must be concise and actionable, with a fixed character limit, so the agent can repair the current stage without reading workflow YAML or guessing the gate definition.
