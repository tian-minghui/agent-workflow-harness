# Condition producers follow package source semantics

A step-local condition producer is a source-backed package asset, not an additional per-task fingerprinted graph artifact. `wf start` continues to bind only the resolved workflow package directory and the SHA-256 fingerprint of `workflow.yaml`. Reference, script, template, asset, and condition-producer files remain directly source-backed: a task run may read the current file, and changing one does not by itself produce a source-drift error.

This preserves the established source-backed package model. The authored workflow YAML names the producer entrypoint, but every `wf next` that needs the fact executes the current package script, just as a workflow-script gate uses its current package source. That is the accepted trade-off: workflow package authors can repair a producer script in place while maintaining the simple package mental model.

The control plane still owns execution and recording. The agent cannot write the runtime fact or routing state directly, but a package script change can affect the next route evaluation because the harness deliberately does not create a task-local script snapshot.
