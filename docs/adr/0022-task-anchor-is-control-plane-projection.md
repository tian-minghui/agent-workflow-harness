# Task anchor is a control plane projection

The repository task anchor at `.workflow-harness/task.json` is a CLI-maintained projection, not an authoritative pointer. The CLI will rebuild or correct it from the control-plane current-task record on start and next; it will remove stale anchors when no active task exists. The agent may read this projection for task preflight but must not edit it.
