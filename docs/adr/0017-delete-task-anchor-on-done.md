# Delete the task anchor on workflow completion

When a workflow reaches its terminal state, the CLI will remove `.workflow-harness/task.json` from the project while retaining the control-plane task history for audit. The file is therefore a pure active-task projection: its presence means the project has an active run, and its absence means the next task may be started. This avoids adding a completed status to the agent-facing anchor schema.
