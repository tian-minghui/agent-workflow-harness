# Workflow creation and execution use separate skills

The harness uses two companion skills with different jobs. `workflow-harness-creator` turns a process design into a source-backed v2 workflow package, including its guide, gates, step-local candidate edges, condition producers, and validation or examples. `workflow-harness-run` remains a thin runner: a bound task uses it only to invoke the control-plane commands and parse the five-status response contract.

The creator skill can explain and author workflow structure because it operates before a task is bound. The runner skill does not absorb those authoring rules because it executes an active task and must not reintroduce the workflow graph, future-stage guides, condition rules, or business deliverables that the agent-blind projection deliberately hides.

The name `workflow-harness-creator` is chosen over `workflow-harness-author` because the skill's product is the complete runnable source package, not just a written document.

`workflow-harness-creator` is manual-only. It must not auto-trigger from ordinary task-progress requests or phrases that merely mention workflows; the user must explicitly invoke the skill, clearly name it, or directly request creation of a workflow package. Ordinary execution and continuation requests remain exclusively the runner skill's responsibility. This prevents a large, file-writing design operation from hijacking an active task.
