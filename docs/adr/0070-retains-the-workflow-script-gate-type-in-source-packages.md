# The workflow retains the `workflow_script` gate type in source packages

A source-backed workflow package keeps the dedicated `workflow_script` gate type. Its `script` path resolves against the resolved source package directory, while its project arguments continue to resolve against the target project root. `${workflowDir}` remains available in model-facing prose and `command` strings, but workflow-scoped scripts do not lose their dedicated gate type or become plain shell commands.
