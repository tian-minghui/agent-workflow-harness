# Human decisions bind to aggregate evidence

A human decision records one aggregate fingerprint over all evidence paths declared by the human gate. Changing any declared path changes the aggregate fingerprint and makes the decision stale for the current step. V1.2 does not track per-file approval or partial freshness, because the human reviewed the combined meaning of the evidence rather than each path independently.
