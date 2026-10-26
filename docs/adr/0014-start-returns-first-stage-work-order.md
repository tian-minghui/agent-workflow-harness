# Start returns the first stage work order

The start command initializes the control-plane instance and immediately returns the first agent-facing stage work order. It does not expose the task ID, workflow path, current step name, or complete workflow. This keeps the model-facing protocol at `workflow start alias → work → next → work → next` without leaking control-plane identity.
