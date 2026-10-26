# Execution tasks and validation range

## 方案拆解

The experiment is broken into four work items. All output stays under the dedicated experiment directory; the core harness implementation is read-only.

## Task 1 — establish evidence container and static baseline

**Deliverables**

- `docs/workflow-validation/skills/static-step.md`
- `docs/workflow-validation/benchmarks/run_cases.py`
- `docs/workflow-validation/benchmarks/tokenize.py`

**Purpose**

Provide the runnable two-mode driver and the static prompt equivalent of the harness workflow.

**Validation**

- The script exits successfully from a clean project root.
- It creates only deterministic files and directories.
- The static prompt includes all stages and prose gates.
- The tokenizer produces equal counts for identical inputs.

## Task 2 — Case A: progression stability

**Deliverables**

- Isolated harness-project sandbox.
- Static-skill decision replay.
- Seeded incomplete-design phase.
- Raw JSON captures under `case-a/runs/`.

**Scenarios**

1. Complete/valid phase input.
2. Incomplete input where the agent attempts premature next-step movement.
3. Stage identity drift attempt.

**Checks**

- Harness must return `blocked` for an unmet staged gate.
- Harness may not report completion for a missing stage.
- Static driver must expose whether premature completion is possible.
- Each raw result remains reproducible after three seeded runs.

**Validation**

- Comparing stage count, blocked count, drift count, and completion identity.
- Case must run without user interaction.

## Task 3 — Case B: gate enforcement

**Deliverables**

- A tiny deterministic project with a real command gate.
- Failing and repaired phases.
- Raw command gate evidence under `case-b/runs/`.

**Scenarios**

1. Test command passes and completion is allowed.
2. Test command fails and completion is blocked.
3. Static-only declaration after a failed command.
4. Repaired command and subsequent completion.

**Checks**

- Harness cannot call final completion while the command exits non-zero.
- Harness requires a deterministic command execution and captures exit status.
- Static mode's false-completion rate must be reported from its declared decisions.
- Raw logs include command output and expected exit code.

**Validation**

- Compare successful completion rate, holistic block rate, required retry count, and false-complete count.
- Case must run without user interaction.

## Task 4 — Case C: usage and token cost

**Deliverables**

- Deterministic inputs for both modes.
- Cost table under `case-c/results/`.
- Summary table in `case-c/results/summary.md`.

**Scenarios**

1. Three stages initiated by a harness work-order sequence.
2. Three stages each receiving the full static prompt.
3. Same stages introduced via a full static instruction, plus a small amount of data.

**Checks**

- Compare per-stage characters and deterministic token estimate.
- Track cumulative input, major context chunk, and control-plane calls.
- Pass/fail ratios are not inferred from cost comparison; they are copied from Cases A/B.
- The same `run_cases.py` invocation produces identical values across repeated runs.

**Validation**

- Case A/B/C results must include a raw size and token count.
- Cost conclusion explicitly separates structural call count from logical progression advantage.

## Task 5 — final report and conversion

**Deliverables**

- `docs/workflow-validation/REPORT.md`
- `docs/workflow-validation/results/case-summary.md`
- `docs/workflow-validation/results/token-cost.md`

**Checks**

- Each claim links to raw case data.
- Each numeric threshold is explicitly defined before reporting.
- The report labels findings as demonstrated, partially demonstrated, or unproven.
- The report contains the launch state, artifact layout, and footnote limitations.
- It states the experiment is isolated and that no core implementation code is modified.

## 测试范围

- Unit-like checks:
  - static prompt stage completeness,
  - tokenizer determinism,
  - task/customer path generation,
  - command gate pass/fail classification.
- Integration:
  - real `wf start` / `wf next` in an isolated control-plane home,
  - real command gate execution in Case B,
  - raw result commitability.
- Repeatability:
  - at least two clean runs,
  - comparing JSON outputs to confirm no incidental stage or runtime mismatch.
- Not in evaluation scope:
  - wall-clock latency as performance proof,
  - quality of actual business artifacts,
  - concurrency behavior outside the tested target session,
  - any comparison involving sticky/branch splits.
