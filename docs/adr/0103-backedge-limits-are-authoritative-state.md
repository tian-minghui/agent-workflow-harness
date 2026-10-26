# Backedge limits are authoritative state

Task state v2 records the minimal execution bookkeeping needed to enforce the conditioned-backedge limit. `visited_steps` is the set of steps entered during the task, and `backedge_counts` maps a source-target transition to the number of times that conditioned route has been selected. These fields are authoritative control-plane state; `wf next` does not scan history or reconstruct the count from an event log.

A selected route is a dynamic backedge when its target already belongs to `visited_steps` and differs from the active step. The control plane permits three selections of the same backedge transition. The fourth attempt evaluates conditions successfully but returns an operational `error` with `backedge_exhausted`; state is not advanced.

History remains an audit log only. Each selected route, including backedge count, is appended to `history.jsonl` for inspection, but mutating history cannot change progression. Timestamps likewise remain history-only and are not stored in the state counters.
