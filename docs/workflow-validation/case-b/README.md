# Case B — command gate enforcement

**Goal:** prove the harness stops at a real `npm test` gate and only advances to `review => done` after the command exits 0.

## Run
```bash
python3 docs/workflow-validation/benchmarks/runner.py --root /tmp/workflow-validation-r4
```

## Raw and summary evidence

- `results/summary.json` — actual `npm test` exit code, stdout, stderr, gate status, retry count, and final workflow status.
- `../results/2026-10-22-r4/raw-run.tar.gz` — full sandbox and all workflows.

## Scenarios

- pass: initial test exit code `0`, harness status `done`.
- fail: initial test exit code `1`, harness status `blocked`.
- repair: initial exit code `1`, repair to `0`, harness reaches `done`.
