# ADR 0001 — Host-agnostic control plane

## Status
Accepted

## Context
The project must guide a coding agent through a deterministic workflow without binding the framework to a single host agent system.

## Decision
The core is a standalone CLI and workflow interpreter. Host-specific adapters are intentionally excluded from v1 so the control plane remains portable across agent runtimes.

## Consequences
The framework cannot physically intercept model tool calls before they occur. Its authority is limited to denying or allowing state progression through the CLI.
