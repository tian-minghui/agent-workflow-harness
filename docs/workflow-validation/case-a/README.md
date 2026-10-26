# Case A — progression stability

**Goal:** prove the harness cannot move from the newest design artifact to implementation while `docs/requirements.md` is absent.

## Run
```bash
python3 docs/workflow-validation/benchmarks/runner.py --root /tmp/workflow-validation-r4
```

## Raw and summary evidence

- `results/summary.json` — parsed case-A summary from the recorded run.
- `../results/2026-10-22-r4/raw-run.tar.gz` — complete isolated sandbox, including every `WF_HOME` and project artifact.

## Expected result

The harness remains `blocked` until the upstream requirement exists; the replayed static-skill case can self-declare completion when conversation drift focuses on the newest artifact.
