# Next without an active task is an error

Running `wf next` when no workflow task is active returns `status: error`, `reason: No active workflow task`, and hint `Run wf start <workflow-alias> --task <title>`. The process exits nonzero. This lets the skill use `next` to discover whether control-plane state exists after a fresh checkout without expanding the response status set.
