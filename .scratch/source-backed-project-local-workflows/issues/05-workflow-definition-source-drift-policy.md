# 05 — Workflow definition source-drift policy

**What to build:** A running workflow is bound to the workflow definition bytes used at start. `wf start` and `wf next` compare the stored fingerprint before resuming or advancing, and any workflow-definition change is reported as an operational error rather than allowing the task to continue against a mutated graph.

**Blocked by:** 01 — Source-backed workflow package resolution; 02 — Project-local runtime state and active-task pointer.

**Status:** ready-for-agent

- [ ] Start records a fingerprint of the workflow definition.
- [ ] Next rereads the same source workflow definition and compares it with the recorded fingerprint before gate evaluation.
- [ ] A same-alias and same-title start resume also verifies that fingerprint before returning the work order.
- [ ] A changed workflow-definition fingerprint returns an `error` result, not a `blocked` result.
- [ ] The runtime state is never silently rebound to the changed workflow definition.
- [ ] Changing a workflow-reference, script, template, or asset file does not trigger workflow-definition drift.
- [ ] The source package remains readable without being copied or snapshotted.
- [ ] Tests create a task, mutate only the workflow definition, and assert error behavior for both `wf start` and `wf next`.
- [ ] Tests confirm non-definition package assets continue to be read directly.
