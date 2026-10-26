# 01 — Human gate schema and pending block

What to build: a workflow author can declare a human confirmation gate inside an existing non-terminal stage. When the stage’s automatic gates have all passed, `wf next` does not advance the stage; it returns `blocked` with stable `HUMAN_REVIEW_PENDING` reason text that carries the human request and all evidence paths. No new response status or structured review object is introduced.

Blocked by: None — can start immediately.

Status: ready-for-agent

- [ ] A workflow can declare a gate whose `type` is `human`.
- [ ] The human gate requires a nonempty `request` and a nonempty list of relative `evidence` paths.
- [ ] Validation rejects a gate with more than one human decision definition in the same step.
- [ ] The conventional human-gate shape is explicit in the workflow schema and remains self-contained:

  ```yaml
  - id: requirements_confirmed_by_user
    type: human
    request: |-
      请确认当前目标、业务边界和验收标准是否符合你的真实预期。
    evidence:
      - docs/requirements.md
  ```

- [ ] The control plane evaluates every automatic gate before the human gate, regardless of YAML order.
- [ ] If an automatic gate fails, the human gate is not reached and the stage stays blocked on that automatic gate.
- [ ] If automatic gates all pass, the human gate blocks and the reason begins with `HUMAN_REVIEW_PENDING`.
- [ ] The blocked reason is a single, deterministic line that contains the workflow request, all evidence paths in declaration order, and the specific `wf approve` / `wf reject` decision commands.
- [ ] All response behavior remains within the existing five-status contract.
- [ ] The test seam is the process-level CLI boundary and does not inspect private internals.
