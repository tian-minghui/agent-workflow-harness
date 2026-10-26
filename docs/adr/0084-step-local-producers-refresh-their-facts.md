# Step-local producers refresh their facts

When the active step declares a producer for a condition variable, route selection must rerun that producer and overwrite the variable's runtime fact. Start inputs and environment aliases with the same logical name do not override this step-local result. The freshly produced value represents the current stage evidence after the step's gates have passed, and it must defeat generic inputs supplied before the task or stage began.

When a later step resolves the same condition variable without a step-local producer, it treats the recorded runtime fact as route evidence and does not rerun the original producer. This distinction is necessary for recovery: a Spec task-assembly step may return to architecture on `routing_gap == true`; when it is entered again and its gates pass, its `routing_gap` producer must inspect the repaired artifacts rather than reuse the stale fact that caused the previous return.

Step-local producers are therefore current-stage evidence writers, while runtime facts act as prior-stage evidence readers. This preserves stage evidence, allows recovery, and still prevents a global mutable-variable surface: the agent never writes the fact, and only the control plane invokes the producer and updates the recorded value.
