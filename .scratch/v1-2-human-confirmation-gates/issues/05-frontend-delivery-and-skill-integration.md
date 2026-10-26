# 05 — Frontend delivery and skill integration

What to build: the built-in `frontend-delivery` workflow gains human gates at the three business-judgment boundaries, and the runner skill teaches the agent how to present the human request and decision commands to the user. The agent still sees only the stage instruction and blocked reason; it never reads the workflow or future stages.

Blocked by: 04 — Human decision audit trail.

Status: ready-for-agent

- [ ] The frontend workflow contains a human gate after `需求澄清`.
- [ ] The frontend workflow contains a human gate after `方案设计`.
- [ ] The frontend workflow contains a human gate before `提PR`.
- [ ] No human gate is added to `任务拆分`, `页面实现`, `自动化测试`, `CodeReview`, or `完成`.
- [ ] Each of the three human gates has an explicit business request and evidence paths.
- [ ] The runner skill explains how to present a `HUMAN_REVIEW_PENDING` blocked reason to the user.
- [ ] The runner skill teaches the agent to request and interpret the human review decision without inventing a new status.
- [ ] The runner skill explicitly preserves the `active / blocked / done / conflict / error` protocol.
- [ ] The runner skill does not expose structured review data, future steps, or future gates.
- [ ] End-to-end verification runs through the existing process-level CLI seam.
