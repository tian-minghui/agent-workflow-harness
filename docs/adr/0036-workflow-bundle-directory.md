# ADR 0036 — Workflow bundles are directory packages

Status: Superseded by ADR 0066

## Status

Proposed

## Context

A workflow alias can require runtime assets in addition to its YAML state-machine definition: a report, a template, or a small resource gate script. A single YAML file cannot represent those assets, and treating a workflow asset as a project-relative path makes an alias depend on the working directory.

## Decision

A built-in or user workflow alias may point to a self-contained workflow bundle:

```text
<alias>/
  workflow.yaml
  resources/
    *.py
    *.md
```

The control plane copies the entire workflow bundle into the task snapshot when the workflow starts. Workflow scripts therefore resolve against `workflow.package` inside the task snapshot, while project files resolve against the target project root.

## Consequences

- A workflow alias is portable across project directories and installed distributions.
- The task snapshot remains the authority for a running workflow, even when the source workflow bundle changes.
- Existing single-file YAML aliases continue to work.
- Runtime code is no longer required to live under the `examples/` directory.
