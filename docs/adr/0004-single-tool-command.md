# ADR 0004 — Single CLI command

## Status
Accepted

## Context
Exposing a large command surface makes an agent more likely to misuse the workflow control plane.

## Decision
The entire v1 interface is one command: `wf next`. The command performs fresh validation, advances on success, and rejects with a reason on failure.

## Consequences
The model has no protocol choices to make. It simply calls the same command whenever it wants to advance or get the next valid guide.
