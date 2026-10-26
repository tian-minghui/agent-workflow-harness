# Human audit metadata lives in history only

V1.2 transition events may reference the human gate, decision, and evidence fingerprint that enabled the transition, but those fields are audit metadata in the append-only history log. They do not extend the model-facing response schema. Commands continue to return only the five-status contract, the active stage instruction, and the existing `check.gate` and `check.reason` fields.
