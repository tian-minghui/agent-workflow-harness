# `wf validate` is a side-effect-free authoring command

`wf validate <workflow-alias>` resolves a source-backed workflow through the normal project → user → built-in package precedence and performs static v2 validation without entering the runtime task contract. It does not create a task, bind a fingerprint, write `.workflow-harness/`, execute normal gates, run condition producers, or interact with the active project task in any way.

The command returns a dedicated authoring result with status `valid` or `invalid`; this is intentionally separate from the five task-execution statuses. A defined workflow need not be started to be reviewed, and validation must remain usable as a feedback loop inside the manual `workflow-harness-creator` workflow.

Validation checks workflow syntax and static graph integrity only. It checks YAML parsing, the v2 version, entry and terminal steps, step-local candidate edges, target references, route grammar, default/when exclusivity, producer path safety, duplicate producer declarations, static reachability from entry to terminal, and absence of the superseded top-level transition list. It does not execute command gates or fact producer scripts, because those belong to runtime progression and can have real side effects.
