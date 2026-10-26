# Approve requires human review readiness

`wf approve` succeeds only when the active step is ready for human review: every automatic gate passes and the human gate is the only remaining blocker. If an automatic gate fails, `wf approve` returns an error and does not record an approval. This prevents an approval from being recorded for evidence that is not yet stable, avoids wasted human attention, and keeps the human decision bound to the final artifacts the workflow intends to review.
