# Human decisions bind to evidence fingerprints

A human gate must declare nonempty `evidence` paths. `wf approve` and `wf reject` store a fingerprint over those paths at decision time, and `wf next` recomputes that fingerprint before accepting the approval. If reviewed evidence changes after approval, the gate blocks again with a stale-approval reason and requires a new human decision. Decisions are therefore bound to the current evidence, not to the step as a permanent authorization.
