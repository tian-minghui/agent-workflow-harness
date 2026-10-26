# ADR 0005 — Event log as fact source

## Status
Superseded by ADR 0068

## Context
State changes need to be auditable and reconstructible across long-running work.

## Decision
Workflow progression is recorded in an append-only event log. The state object is a derived projection, not an independent source of truth. Every successful or failed attempt contributes a history event.

## Consequences
The task directory can be rebuilt or verified from history. Integrity and simplicity of the history log are primary quality attributes.
