# Conditioned backedges have a fixed cycle guard

The same conditioned backedge may be selected at most three times in one task. The fourth attempt returns an `error` response and records `backedge_exhausted` with the source step, target step, condition variable, and observed cycle count. This is an operator-visible safety guard, not a business-run metric and not a sixth response status.

The first conditional-routing version deliberately does not expose a per-edge `max_cycles` setting or attempt to infer whether intervening project evidence changed meaningfully between loops. A semantic-diff gate would duplicate gate responsibilities and add a new judgment area; a configurable limit would invite every workflow to tune one more parameter before learning whether the backedge itself is modeled correctly. If experience shows that three cycles are too restrictive for a legitimate workflow, the limit can be revisited with evidence rather than extended speculatively.
