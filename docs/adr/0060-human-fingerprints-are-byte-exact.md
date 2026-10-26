# Human fingerprints are byte-exact

V1.2 fingerprints the exact bytes of the declared evidence. A whitespace-only, formatting-only, or otherwise cosmetic change produces a different fingerprint and invalidates a prior approval or rejection as a decision for the current evidence. The control plane intentionally does not decide whether a change is semantically significant; requiring another review is safer and simpler than guessing equivalence.
