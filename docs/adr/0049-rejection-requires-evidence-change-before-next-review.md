# Rejection requires evidence change before the next review

After a human rejects a step, a new human review may be requested only after the declared evidence changes. If `wf next` observes that the current evidence fingerprint still matches the rejected fingerprint, it remains blocked and reports that no new evidence exists for another review. A changed fingerprint invalidates the rejection as a transition condition but does not act as approval; the human must approve the new evidence before the step can advance.
