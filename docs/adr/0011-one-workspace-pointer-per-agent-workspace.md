# One workspace pointer per agent workspace

Status: superseded by ADR-0012.

The initial direction was to place a pointer in each agent workspace. This was replaced by a single current-task pointer in the project root so the CLI can resolve the run from the current project without exposing or passing a task directory.
