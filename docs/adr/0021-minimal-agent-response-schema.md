# Minimal agent response schema

V1.1 response objects will stay minimal and stable:

- `active`: `status`, `task.title`, `instruction`
- `blocked`: `status`, `task.title`, `instruction`, `check.gate`, `check.reason`
- `done`: `status`, `task.title`
- `conflict`: `status`, `active_task.title`, `reason`, and optional `hint`
- `error`: `status`, `reason`, and optional `hint`

Responses never include task IDs, step names, transitions, workflow paths, complete gate lists, future guides, state paths, or history paths. Blocked responses are repair orders for the current stage; they never provide the next stage.
