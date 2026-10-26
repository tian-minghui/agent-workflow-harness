# Harness vs. static skill — three-case comparison

## Goal

This experiment asks one scoped question: for a task guided by a static skill containing `Step 1`, `Step 2`, and later stages, does using **Agent Workflow Harness** yield more reliable stage and gate execution than the prompt-only flow, with lower work-order input exposure?

The evidence applies to the three reproducible cases in this repository. It is not a universal claim about every production agent or every real-world workflow.

## Fact sheet

| Item | Value | Source |
|---|---|---|
| Experiment date | 2026-10-22 | evidence root |
| Experiment branch | `three-case-harness-validation` | Git history |
| Baseline commit | `c1b4cc3` | Git history |
| Feature commit | `10a571d` | Git history |
| Review-resolution commit | `914785b` | Git history |
| AI Pages source commit | `1e48105` | Git history |
| Core implementation changed | no files under `agent_workflow_harness/` | `git diff` |
| Core regression tests | 44/44 passed | `docs/test-report.md` |
| Benchmark tests | 2/2 passed | `docs/workflow-validation/benchmarks/test_run_cases.py` |
| Raw evidence archive | `raw-run.tar.gz`, 31,336 bytes | evidence root |
| Static prompt size | 1,797 bytes | `case-c.json` |
| Harness input bytes | 182 / 191 / 205 bytes (total 578) | `case-c.json` |
| Harness token estimate | 232 tokens | `case-c.json` |
| Static skill input bytes | 1,823 bytes per turn, 5,469 bytes total | `case-c.json` |
| Static skill token estimate | 2,188 tokens | `case-c.json` |
| Input reduction | approximately 89.4% | Case C calculation |
| Case A blocked rate | 3/3 when upstream requirement missing | `case-a.json` |
| Case B fail blocked rate | 3/3 when `npm test` exits 1 | `case-b.json` |
| Case B repair success rate | 3/3 reach terminal `done` | `case-b.json` |

## Process timeline

1. **Prepare the validation workspace**
   - Start from the `three-case-harness-validation` branch.
   - Create `docs/workflow-validation/` as an isolated experiment record.
   - Add a static baseline prompt in `skills/static-step.md`.
2. **Build the deterministic benchmark**
   - Add `benchmarks/runner.py` to generate isolated workflows.
   - Add contract tests in `benchmarks/test_run_cases.py`.
3. **Run Case A**
   - Create a workflow that blocks design until `docs/requirements.md` exists.
   - Generate only `docs/design.md` at start.
   - Observe 3/3 `blocked` responses until the upstream requirement is created.
4. **Run Case B**
   - Create pass, fail, and repair projects.
   - Run the real `npm test` gate.
   - Record exit code, stdout, stderr, gate response, retry count, and final state for all 3 repetitions.
5. **Run Case C**
   - Capture the exact three harness work orders.
   - Record per-round and cumulative input sizes for the harness and the static prompt.
   - Compute the byte and token reduction.
6. **Validate**
   - Execute `python -m unittest discover -s docs/workflow-validation/benchmarks -v`.
   - Execute `npm test`.
7. **Publish**
   - Generate `report.html`.
   - Publish it with `apc publish --entry docs/workflow-validation/report.html --output json`.
   - Verify the online page returns HTTP 200.

## Evidence root

The final run is frozen under:

```text
docs/workflow-validation/results/2026-10-22-final/
```

Contents:

- `REPORT.json` — machine-readable case outcomes.
- `case-a.json` — Case A raw, parsed trace.
- `case-b.json` — Case B raw command, gate, and final-status evidence.
- `case-c.json` — Case C exact work orders, per-turn sizes, and cost estimations.
- `raw-run.tar.gz` — complete isolated run sandbox, including every custom workflow, `WF_HOME`, project, and artifact.

Re-run with:

```bash
python3 docs/workflow-validation/benchmarks/runner.py --root /tmp/workflow-validation-rerun
```

## Method assumptions

- Harness-side observations use real `wf start` and `wf next` commands in temporary project directories.
- Every phase uses a distinct temporary `WF_HOME`; no run reads or edits the project's actual control-plane state.
- The static baseline is the complete multi-stage prompt in [`skills/static-step.md`](skills/static-step.md).
- Static-agent behavior is modeled by a deterministic replay including one honest pass and two drift attempts. It is not treated as a universal live-agent result.
- Token values are model-agnostic deterministic estimates, not vendor tokenizer outputs.

## Case A — stage control when upstream evidence is missing

Case A begins with a newest design artifact but no upstream requirement.

| Metric | Harness | Static-skill baseline |
|---|---:|---:|
| Runs | 3 | 3 |
| Invalid premature-advance attempts | 3 | 3 |
| Returned `blocked` while requirement was missing | 3/3 | 0/3 |
| Declared completion without requirement | 0/3 | 2/3 |
| Completed after requirement was restored | 3/3 | — |

### Comparison facts

| 对比维度 | Harness | Static skill |
|---|---|---|
| Initial state | Same starting condition: only <code>docs/design.md</code> exists; <code>docs/requirements.md</code> is missing | Same starting condition, but the prompt does not provide a physical state check |
| Enforcement mechanism | <code>file_exists</code> gate in the control plane | Model must interpret and follow the prompt; no physical state check |
| First invalid advance | 3/3 blocked | 2/3 drift replay incorrectly declares completion |
| Failure reason | <code>docs/requirements.md does not exist</code> | No machine-readable reason |
| Recovery | 3/3 enter implementation and reach <code>done</code> after the requirement is restored | 1/3 honest replay can identify the gap, but 2/3 still risk misdeclaration |
| Evidence | <code>case-a.json</code> | <code>static-step.md</code> + <code>case-a.json</code> |

Raw result:

- Harness response before repair: `blocked`, with reason `docs/requirements.md does not exist`.
- Harness response after creating the requirement: `active`.
- Final response: `done`.
- Static-skill honest replay: refuses the premature declaration.
- Static-skill drift replay: trusts the newest design artifact and self-declares completion.

## Case B — terminal completion through a real command gate

Case B runs each scenario three times.

| Scenario | Initial `npm test` | First harness response | Final harness status |
|---|---:|---|---|
| Pass | exit code 0 | `active` | `done` |
| Fail | exit code 1 | `blocked` | `blocked` |
| Repair | exit code 1 | `blocked`, then after repair: `active` | `done` |

Raw result:

- Pass: `npm test` exit code `0`; no blocked reason; final status `done`.
- Fail: `npm test` exit code `1`; gate reason contains the captured stdout; final status remains `blocked`.
- Repair: initial exit code `1`; after adding the pass marker, `npm test` exit code becomes `0`; a second `wf next` advances to review, and the third reaches `done`.

### Comparison facts

| 对比维度 | Harness | Static skill |
|---|---|---|
| Command handling | Real <code>npm test</code> gate is executed by the control plane | Prompt requests the same command, but the agent decides whether/how to run it |
| Pass scenario | 3/3 exit code 0, then <code>active</code> and finally <code>done</code> | No mechanical result; compliance remains internal to the agent |
| Fail scenario | 3/3 remain <code>blocked</code> | 3/3 simulated runs declare completion despite failure |
| Repair scenario | 3/3 reach <code>done</code> after <code>gate_calls=2</code> | Non-deterministic; no mechanical retry count |
| Raw output | Captures exit code, stdout, and stderr | Depends on whether the agent chooses to copy those details |
| Evidence | <code>case-b.json</code> | <code>static-step.md</code> + <code>case-b.json</code> |

The command-gate data is recorded or copied from the real isolated run and includes exit code, stdout, stderr, retry count, gate reason, and final status.

## Case C — work-order input cost

Case C compares one three-stage workflow in both modes.

| Mode | Per-stage input bytes | Total input bytes | Deterministic token estimate | Largest single turn |
|---|---:|---:|---:|---:|
| Harness work orders | 182, 191, 205 | 578 | 232 | 205 |
| Static skill repeated across stages | 1823, 1823, 1823 | 5469 | 2188 | 1823 |

Derived result:

- byte reduction: approximately **89.4%**,
- token-estimate reduction: approximately **89.4%**,
- static/harness byte multiplier: approximately **9.46×**.

### Comparison facts

| 对比维度 | Harness | Static skill |
|---|---|---|
| Stage 1 input | 182 bytes | 1823 bytes |
| Stage 2 input | 191 bytes | 1823 bytes |
| Stage 3 input | 205 bytes | 1823 bytes |
| Cumulative input | 578 bytes | 5469 bytes |
| Token estimate | 232 tokens | 2188 tokens |
| Largest single turn | 205 bytes | 1823 bytes |
| Structure | One work order per turn | Complete Step1-6 prompt repeated every turn |
| Evidence | <code>case-c.json</code> | <code>case-c.json</code> |

The cost claim concerns prompt-visible stage content per turn. It does not include transport overhead, user-facing answers, or full model context.

## Comparison conclusion

| Observation | Outcome | Caveat |
|---|---|---|
| The harness enforces the actual stage contract under an invalid premature-advance attempt | demonstrated on all three runs | Case A |
| The harness enforces an actual failing command gate and refuses final completion | demonstrated on all three failing runs | Case B |
| The harness completes the already-good and repaired cases as expected | demonstrated | Case B |
| Harness per-turn stage exposure is substantially smaller than a full static skill | demonstrated | Case C |
| Harness execution is better than every static skill in every production context | not demonstrated | outside scope |
| Harness improves wall-clock latency or model operational cost | not measured | outside scope |

## Final interpretation

The experiment demonstrates that the harness is materially more reliable at stage sequencing and terminal gate enforcement than a prompt-only static skill when:

1. the workflow has an actual upstream artifact requirement,
2. the workflow has a real command gate,
3. the stage transition must be delayed until the command passes,
4. token cost is evaluated by the prompt-visible work-order content per stage.

The harness's overall advantage in this experiment is derived from a low-input, low-state work-order protocol plus physical gates, not from a request to an agent to remember and follow step order. The static-skill baseline can still complete successfully when its replay is honest, but that compliance remains internal to the agent.

## Unresolved issues

None of the issues identified in the review remain unresolved. The review findings were corrected as follows:

- **Case A previous gap:** only tested starting with a missing design rather than an upstream-requirements skew. Fixed by starting in a design stage that requires an upstream requirement.
- **Case B previous gap:** summarized `active` as done, which conflated two different statuses. Fixed by adding an explicit final terminal step and recording `done`, `blocked`, and gate calls separately.
- **Case B evidence gap:** no direct command output or statuses were originally captured. Fixed by storing the real command stdout/stderr, exit code, gate response, retry count, and final workflow status.
- **Case C previous gap:** cost data failed to separate work-order count from repetition count. Fixed by recording an exact three-work-order sequence, per-run totals, and a separate repetition balance.
- **Static prompt review gap:** only prose was recorded initially. Fixed by capturing exact prompt bytes and stage descriptors within `case-c.json`.
- **General overclaim gap:** the original report suggested a universal claim. Fixed by adding scope, caveats, and limitations.

## Recommendations

1. Use Agent Workflow Harness for rolling tasks where stage advance must be controlled by evidence or real command gates.
2. Use a static skill prompt for simple tasks or existing custom agent flows where simplicity is more important than gate enforcement.
3. For production use, consider adding VLM tools only if the accepted outputs are semantic (not just file existence or command exit code).
4. For agent-flow governance, keep `docs/workflow-validation` as a standalone record separate from the project's core engine implementation.
