# Experiment design — harness-driven vs static-skill-driven execution

## 方案

本实验使用三个隔离场景（顺序推进稳定性、真实门禁可靠性、上下文/token成本），通过可重复脚本分别驱动同一目标在 harness 与静态 skill 两种模式下的执行，并将原始结果和结论沉淀在单一实验目录中。

Define the experiment infrastructure needed to compare the two execution modes under three sequential workflows and preserve professional/skill-user context integrity across only one task.

## Experimental architecture

The test consists of three sequential, isolated workflows. Each case must start from an initial `docs/design.md` artifact and a valid staging baseline with no task switch, through one terminal prompt. Only the first case is allowed to require a live session; its result is used as a twin-commit seed for cases two and three.

Each case uses two virtual workflow engines:

1. **Harness mode** — the real Agent Workflow Harness CLI, isolated by `WF_HOME` and a dedicated task/project directory.
2. **Static-skill mode** — a deterministic prompt containing the complete stage sequence and gate requirements; the controlplane calls a simulated agent that may advance or mistakenly relabel evidence.

The harness side uses actual workflows up to the stage where the gate blocks or permits completion. The baseline side uses the equivalent prose instructions and a deterministic test runner that interprets compliance.

## Workflow DAG summary

```text
case A (progression stability)
  workflow stage 1: design
    ├── harness: next is blocked until the design artifact contains required content
    └── static: next advances on the simulated agent's self-declaration

case B (gate enforcement)
  workflow stage 1: build/implementation
    ├── harness: command gate must pass
    └── static: tests are required by prompt but not physically enforced
  workflow stage 2: gate completion
    ├── harness: checked against actual command/gate execution
    └── static: checked only against declared output

case C (token/context cost)
  workflow stages 1-3
    ├── harness: every stage exposes one minimal work order
    └── static: every stage begins with the complete static prompt
```

## Data state

The experiment keeps state on disk, not in memory or hidden control-plane texts:

- `docs/workflow-validation/case-a/`
  - `input/` — seeded plan and optional partial files
  - `runs/` — one recorded run per comparison
- `docs/workflow-validation/case-b/`
  - `input/` — command and gate definitions
  - `runs/` — raw test outputs and gate results
- `docs/workflow-validation/case-c/`
  - `inputs/` — the exact harness work orders and static prompt
- `docs/workflow-validation/results/`
  - generated raw artifacts and final tables

The benchmark uses a `run_case_a.py`-style script and a `run_case_b.py`-style script. Results always resolve through one of two canonical time formats, as required by the current project state. The command payload is executed from one place and never duplicated.

## Commands and drivers

### Static-skill prompt

Create `docs/workflow-validation/skills/static-step.md` containing complete step-by-step instructions:

- Step 1: requirements
- Step 2: design
- Step 3: implementation
- Step 4: gates/tests
- Step 5: review/summary
- Step 6: commit

The prompt includes prose gates such as “do not complete Step 4 until the command exits 0.” This is the honest baseline: it contains all instructions, but the completion declaration remains with the agent.

### Harness driver

A deterministic driver in `docs/workflow-validation/benchmarks/run_cases.py`:

- creates an isolated temporary project/control-plane home,
- copies only the harness artifact model into an isolated project,
- invokes `wf next`,
- records the five-status JSON result,
- classifies the stage outcome,
- composes raw metrics and writes one summary row per case.

### Static-skill driver

The same script runs the static prompt through a deterministic simulated agent:

- reads the complete step list,
- checks the current artifacts,
- may mis-distinguish “created file” from “gate passed” deterministically on seeded intervals,
- has no control-plane history or stage authority,
- records its own JSON decisions.

## Comparison methodology

### Case A — progression stability

- Input:
  - design stage scope and expected keywords
- Compare:
  - ordered completion identity
  - illegal transition attempts
  - status distribution and extra `wf next` calls
  - reproducibility across seeded runs
- Record:
  - raw commands and JSON outputs for each comparison
- Output metrics:
  - correct stage path count
  - stage drift count
  - blocked calls before completion
- Human or reviewer time is not used as a workflow metric.

### Case B — gate enforcement

- Input:
  - implementation with a real test command
  - invalid test result
- Compare:
  - whether the harness blocks when tests fail and only completes after a fix
  - whether the static skill self-declares completion or takes a shortcut
- Record:
  - command stdout exit codes
  - failed/gate statuses
  - number of manual retries
- Output metrics:
  - successful terminal completion rate
  - false complete rate
  - gate preventive rate

### Case C — token/context cost

- Input:
  - harness work-order content per stage
  - static-skill prompt plus current content descriptor
- Compare objective skill input cost:
  - characters and approximate tokens
  - cumulative input string size
  - serialized JSON size
  - duplicate content introduced by repeated full prompt presentation
- Use a deterministic tokenizer so exact token counts can be regenerated from the raw input set.
- Record both raw sizes and normalized table output.

## Reproducibility

`run_cases.py` must create all inputs programmatically. It must seed a fixed test delay line and a deterministic test outcome before each command, so repeated runs are identical. No environment variables are required to reproduce the experiment, and all paths stay relative to the script's known root to ensure one working directory is used consistently.

## Expected observations

- Harness mode should show more stable *ordinal/status* flow, especially when stage outputs are incomplete.
- Harness mode should reliably block on a false gate, while static-skill mode can report path completeness even when actual gate content is invalid.
- Harness mode should expose less text at each step, but may incur slightly higher context/token usage relative to workflow volume due to control-plane call mechanics.
- The long-run viability of either mode is measured by stage identity integrity and task completion, not only by total inputs.

## Definition of done

The experiment is complete when `docs/workflow-validation/REPORT.md` contains:

- three final tables and any per-step/appendix observations,
- an honest summary of which claim is demonstrated, weakly demonstrated, or not demonstrated,
- a recursion tree showing the comparison source for each metric,
- reproducibility instructions,
- a note that the project’s core harness remains unchanged throughout development.
