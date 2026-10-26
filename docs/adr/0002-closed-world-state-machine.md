# ADR 0002 — Closed-world workflow state machine

## Status
Accepted

## Context
The workflow model must prevent the agent from inventing stages or redirecting progress informally.

## Decision
Workflow YAML defines every step, transition, and gate explicitly. The CLI does not synthesize new steps, routes, or conditions.

## Consequences
Any workflow intent not declared in YAML is invalid. The task cannot progress to an undeclare destination. Conditions and dynamic routing are out of scope for v1.
