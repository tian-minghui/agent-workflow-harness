# Case C — per-turn input cost

**Goal:** compare the model-visible work order for one three-stage workflow with the full static skill prompt repeated at each of the three equivalent stages.

## Run
```bash
python3 docs/workflow-validation/benchmarks/runner.py --root /tmp/workflow-validation-r4
```

## Raw and summary evidence

- `results/summary.json` — exact work orders, per-turn byte counts, cumulative byte counts, and deterministic token estimates.
- `../results/2026-10-22-r4/raw-run.tar.gz` — complete isolated sandbox.

## Interpreting the metric

The harness count is a single workflow's 3 work orders. The run blocks are repeated 3 times and reported separately as evidence of stability, not added to the single-workflow cost.
