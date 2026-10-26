# ADR 0006 — v1 scope boundary

## Status
Accepted

## Context
The project must remain small enough to build correctly while covering the essential deterministic workflow control-plane behavior.

## Decision
v1 excludes permissions enforcement, external databases, parallel transitions, conditional routing, evidence file systems, action constraints, host hooks, and rich event trails. It supports a single, linear, explicit state machine with fail-fast gates.

## Consequences
The framework gains simplicity and auditability at the cost of advanced workflow control. Future versions can add those capabilities without changing the already fixed core semantics.
