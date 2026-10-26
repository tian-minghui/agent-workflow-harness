# English task titles are a breaking contract

The stricter task-title protocol is applied as a clean breaking change. New tasks must use a natural English title of 5–120 ASCII letters, digits, spaces, and hyphens. Existing task state that contains a nonconforming title is not transliterated, translated, normalized into a legacy slug, or resumed under a second legacy title contract.

A workflow run created by an older harness version with a nonconforming title therefore returns an operational error when the new harness tries to load or resume it. The error should direct the operator to preserve any useful evidence and start a replacement task with a valid English title. This keeps one title contract and one deterministic artifact-directory rule rather than maintaining parallel title and template-variable behavior inside the same runtime.

The task-state schema string remains `agent-workflow-harness.task-state.v2`; schema-v3 is not introduced. The current v2 contract is still being established and its state format is revised in place to make `artifact_dir` required. State written by the preceding v2 implementation is rejected by the new v2 integrity checks because it lacks the required artifact-directory fact and may carry a nonconforming title. The schema string therefore identifies the current v2 format, not an open-ended compatibility family across pre-release revisions.
