# Human gates require an explicit request

A `type: human` gate declares a `request` message in addition to its `evidence` paths. The request is the business question the human is being asked to answer; the evidence is the artifact fingerprint the decision is bound to. A generic "confirm this stage" prompt is not enough because it loses the concrete decision context that makes human review useful.
