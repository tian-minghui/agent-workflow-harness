# Static skill: three-stage frontend delivery

You are executing a complete frontend delivery process from one prompt. Do not stop after a single stage; read all steps and decide which step is current.

## Step 1 — Requirements

Collect the user-visible outcome, interaction scope, acceptance criteria, constraints, and compatibility requirements. Save them in `docs/requirements.md` before moving to Step 2.

## Step 2 — Design

Explain the page structure, interaction flow, state and data design, component boundaries, error states, and implementation strategy. Save the result in `docs/design.md` before moving to Step 3.

## Step 3 — Implementation and staged work orders

Turn the approved design into concrete, testable work orders. Record task boundaries, test scope, implementation decisions, and test report locations in task metadata. Do not proceed until the current stage artifact is complete.

## Step 4 — Automated tests and gates

Run the project’s automated test command. For this benchmark, `npm test` must pass before delivery may be declared complete. If it fails, fix the implementation, rerun `npm test` or equivalent platform command, and record the attempt. Do not treat a skipped, unknown, or partially observed test result as a pass.

## Step 5 — Code review and review convergence

Review the resulting code and artifacts, list standards and spec issues, remove non-action TODOs, and only complete this step when every issue is either resolved or explicitly documented in the release report.

## Step 6 — Delivery and PR

Prepare the PR metadata and other PR readiness data. Record `Implementation complete`, `Tests passed`, and `Review complete` in the implementation notes. Only after those facts are verified may you declare the whole workflow complete.
