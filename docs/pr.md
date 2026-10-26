# PR readiness — three-case harness validation

## Basic information

- **Repository**: local repository `agent-workflow-harness`
- **Source branch**: `three-case-harness-validation`
- **Target branch**: `main`
- **Task title**: Deliver three-case harness validation
- **Suggested PR title**: `feat: 三场景验证 workflow harness 优于静态 step 流程`
- **Work item**: not attached
- **Reviewers**: not configured in this local-only repository
- **PR status**: local merge-ready

## Why this PR is ready locally

The source branch is based on `main` and contains two commits:

```text
c1b4cc320697a4d  docs: add external workflow comparison research
10a571d  feat(validation): compare harness and static skill flows
```

The actual feature commit is `10a571d`; `c1b4cc3` is the pre-task baseline commit required before executing the three-case validation. The diff therefore isolates the three-case experiment and its supporting evidence.

There is no origin remote configured, so no actual GitHub/GitLab PR can be created from this workspace. This file preserves the merge-ready PR metadata and can be used directly once a remote PR repository and reviewers are configured.

## Suggested PR description

```markdown
## Summary

Add a standalone, reproducible three-case comparison between Agent Workflow Harness and a static multi-stage skill:

1. Case A records stage control when a design artifact exists but an upstream requirement is missing.
2. Case B records real `npm test` gate failure, repair, review, and terminal `done` progression.
3. Case C records per-stage work-order input bytes and deterministic token estimates versus the full static prompt.

## Evidence

- `docs/workflow-validation/REPORT.md`
- `docs/workflow-validation/results/2026-10-22-final/`
- `docs/workflow-validation/results/2026-10-22-final/raw-run.tar.gz`
- `docs/workflow-validation/benchmarks/runner.py`

## Tests

- `python -m unittest discover -s docs/workflow-validation/benchmarks -v`
- `npm test`
- Project regression suite: 44/44 passed

## Boundary

No code under `agent_workflow_harness/` was modified for the experiment.

## Claims

The experiment demonstrates the scoped advantage of harness-driven stage and gate control, not a universal comparison of every static skill or production agent.
```

## Notes

- Core implementation files under `agent_workflow_harness/` are unchanged.
- Root-level `package.json` is a minimal `npm-test` alias required by the current machine-checked workflow queue.
- The task branch and evidence directory keep the experiment distinguishable from core runtime changes.
