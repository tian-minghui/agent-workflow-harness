# Three-case harness validation record

This directory is the standalone, executable record for **“Deliver three-case harness validation.”** The experiment compares:

1. **Agent Workflow Harness** — current work order plus physical gates.
2. **Static skill** — one full multi-stage `Step 1/Step 2/…` prompt with no physical control plane.

## Entry points

- [`REPORT.md`](REPORT.md) — final tables, claims, conclusions, limitations, and review resolution.
- [`benchmarks/runner.py`](benchmarks/runner.py) — reproducible, isolated, CLI-driven experiment.
- [`benchmarks/test_run_cases.py`](benchmarks/test_run_cases.py) — benchmark contract tests.
- [`skills/static-step.md`](skills/static-step.md) — complete static-skill baseline prompt.
- [`case-a/`](case-a/) — progression-stability record.
- [`case-b/`](case-b/) — `npm test` gate-enforcement record.
- [`case-c/`](case-c/) — work-order/cost comparison record.
- [`results/2026-10-22-final/`](results/2026-10-22-final/) — frozen machine-readable outputs and full raw `raw-run.tar.gz` sandbox.

## Reproduce

```bash
python3 -m unittest discover -s docs/workflow-validation/benchmarks -v
python3 docs/workflow-validation/benchmarks/runner.py --root /tmp/workflow-validation-rerun
```

The benchmark script creates its own sandboxed `WF_HOME` and temporary projects. It does not modify `agent_workflow_harness` source code.

## Protection boundary

No internal `agent_workflow_harness` source implementation was changed for this experiment. Root-level `package.json` exists only as a minimal `npm test` alias for the current workflow’s machine-checked stage gate, and forwards to `python3 -m unittest discover -v`.
