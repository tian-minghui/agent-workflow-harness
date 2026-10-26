# Route evaluation is a state transaction

`wf next` evaluates a step’s conditional route in memory. It runs the required step-local condition producers, resolves their scalar values, evaluates candidate edges, selects one route, and checks the fixed backedge cycle limit. If any part of that evaluation fails-producer error, unresolved condition, multiple matching edges, missing arbitration, or an exhausted backedge-the command returns an `error`, appends an audit event, and leaves the authoritative task state unchanged.

Only a successfully selected route performs one authoritative state write. That write updates the new step, accepted runtime facts, visited-step set, and backedge counters together. Producer output from an unsuccessful attempt is not persisted in `state.facts`, because the active step’s producer reruns before every route selection and facts represent controls applied to a successful route rather than every intermediate attempt.

History remains the audit source for failed evaluation attempts and may record the resolved condition values that were observed before the error. It is not a recovery source and cannot alter authoritative state.
