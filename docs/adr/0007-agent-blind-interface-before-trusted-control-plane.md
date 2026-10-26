# Agent-blind interface before a trusted control plane

V1.1 will minimize what the model normally sees—workflow YAML, future steps, and future guides—by exposing only an agent-blind active-stage interface. This is explicitly information minimization rather than a hard security boundary; deliberate filesystem access can still bypass it. A trusted control plane using a server, MCP tool, or host sandbox is deferred to a later version.
