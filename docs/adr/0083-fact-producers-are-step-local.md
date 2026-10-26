# Fact producers are step-local

A fact producer is declared on the step whose outgoing condition may require its value. The step does not declare a global variable or a cross-workflow type; it declares how the control plane can lazily derive a named condition value while selecting one of that step's outgoing edges.

Placing producers at step scope preserves the intended lifecycle. The producer runs only after that step's ordinary gates pass, and before the step's candidate edges are arbitrated. A start input or environment value avoids producer execution entirely. Once the control plane records the resulting runtime fact, later steps can resolve that fact by logical name without rerunning the producer.

A logical condition variable may have at most one producer declaration in a workflow. This keeps the same condition name from changing meaning between steps and avoids recreating the global mutable-variable model that conditional routing deliberately avoids. If a later stage needs a new judgment, it should use a new condition-variable name and its own step-local producer.
