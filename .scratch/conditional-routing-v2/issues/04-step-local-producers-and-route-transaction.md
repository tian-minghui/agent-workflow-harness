# 04 — Step-local producers and route evaluation transaction

**What to build:** produce condition facts from workflow package-owned scripts and commands, then route through them as an atomic state transaction. This slice makes a conditional route that runs without reusing or modifying agent-written facts, while preserving human gates and distinguishing false evaluation from failure.

**Blocked by:** 03 — Start inputs and condition-value resolution.

**Status:** done

- [ ] A step can declare a lazy condition producer for a variable used by one of its outgoing edges.
- [ ] A logical condition variable has at most one producer in the workflow.
- [ ] Producer execution happens only after the active step’s ordinary gates and human gate pass.
- [ ] `wf approve` does not invoke a producer or advance the stage.
- [ ] A workflow-script producer exits zero and emits exactly one nonempty single-line scalar.
- [ ] Bare `true` and `false` producer results are persisted and compared as Boolean; other scalar results are compared as exact strings.
- [ ] A command producer maps exit 0 to true, exit 1 to false, and exit 2 or greater to `error`.
- [ ] Malformed producer output, non-zero exit, timeout, or failure is an `error`, never `false`.
- [ ] A workflow-level integer `producer_timeout_seconds` supports the 1–300 range, defaults to 30, and applies to all producers in that workflow.
- [ ] The workflow only writes the accepted fact to state after route arbitration and the back-edge limit succeed.
- [ ] Producer failure, multiple candidate matches, or back-edge exhaustion preserves the current step, facts, visited steps, and back-edge counters.
- [ ] An active-step producer reruns before every route selection from that step, and later steps reuse the previously recorded runtime fact.
