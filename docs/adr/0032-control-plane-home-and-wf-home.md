# Control plane home and WF_HOME

Status: Superseded by ADR 0067

The control-plane home defaults to `~/.workflow-harness/` and may be overridden with the `WF_HOME` environment variable. The override is required for unit and integration isolation. The home contains the user workflow catalog, project namespaces, current task pointers, and task instances.
