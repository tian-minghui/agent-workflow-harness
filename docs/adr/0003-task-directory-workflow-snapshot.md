# ADR 0003 — Task directory as workflow instance

## Status
Accepted

## Context
A workflow run needs a stable, self-contained context that can survive repeated agent sessions.

## Decision
Each workflow run lives in a dedicated task directory. That directory holds the workflow snapshot, lock file, derived state, and history log. The snapshot is copied at initialization, so later changes to the original YAML do not affect an active run.

## Consequences
A running workflow is portable and auditable. Upgrading a workflow after initialization requires a new run or an explicit future migration path, which v1 does not provide.
