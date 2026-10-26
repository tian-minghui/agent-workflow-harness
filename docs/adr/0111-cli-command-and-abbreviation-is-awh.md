# The CLI command and abbreviation is `awh`

The console command for agent-workflow-harness is `awh`, pronounced and written as the workflow's official abbreviation. The package keeps its full name `agent-workflow-harness`, but all user-facing command references use the short form.

## Decision

- The sole installation entry point is `awh = agent_workflow_harness.cli:main`.
- `awh start`, `awh next`, `awh validate`, `awh approve`, `awh approve --next`, and `awh reject` replace the former `wf ...` spellings.
- The operator-only project override becomes `AWH_PROJECT_DIR`, replacing `WF_PROJECT_DIR`.
- Skill triggers mention `awh` explicitly: requests such as “使用 awh 工作流完成 xxx” must select the runner skill.
- The `WF_<VARIABLE>` environment-condition alias prefix for workflow condition variables is a separate published condition-resolution contract and stays unchanged.
- No compatibility shim is installed. A machine that still has an old `wf` executable should reinstall the harness; new installs provide only `awh`.

Earlier ADRs and historical reports that mention `wf` describe the state of the system at their time and are not rewritten.
