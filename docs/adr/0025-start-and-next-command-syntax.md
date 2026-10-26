# Start and next command syntax

Start will use `wf start <workflow-alias> --task <title>`, where the workflow alias is the required positional selector and the task title is a required quoted option. Next will use `wf next` with no model-facing path or directory arguments. The runtime resolves the project and active run from the current working directory, with an operator-only `WF_PROJECT_DIR` override.
