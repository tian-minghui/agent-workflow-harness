# Clean v1.1 breaking change

V1.1 will replace the v1 workflow-directory protocol instead of maintaining a compatibility layer. The old `--workflow`, `--task-dir`, and task-directory state layout will be removed. The only agent-facing protocol will be `wf start <workflow-alias> --task <title>` and `wf next`. Existing v1 runs will remain historical records; continuing them through v1.1 is not supported.
