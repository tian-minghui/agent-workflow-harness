# Separate agent workspace from a project-namespaced control plane

Status: Superseded by ADR 0067

The agent workspace and the control-plane instance are separate concepts. The workspace holds model-produced artifacts visible to the agent; the CLI owns snapshot, state, history, and lock data in its own local control-plane home, organized by the project directory associated with the run. This partially supersedes the v1 self-contained task directory and establishes the local precursor to a later trusted control-plane service.
