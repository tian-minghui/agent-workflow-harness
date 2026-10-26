# Resume preserved task inputs

A matching `wf start` resumes the active task when its workflow alias and normalized task title match. The request may omit `--var` entirely, or it may repeat exactly the variables and values recorded when the active task was created. In both cases, start returns the current work order without changing task state.

Supplying a value different from the recorded input, adding a variable that was not originally recorded, or otherwise proposing a different condition-vector set returns `conflict`. Start does not mutate the active task’s inputs, start a replacement task, or choose silently between the old and new routes. Duplicate use of the same variable name in one command is an argument `error`; no task state is created or changed.
