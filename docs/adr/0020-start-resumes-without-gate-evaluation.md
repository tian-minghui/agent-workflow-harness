# Start resumes without gate evaluation

Start may create a new task or resume the active task when the workflow alias and title match exactly. In both cases it returns the current work order and never evaluates gates or advances state. Gate evaluation and progression remain exclusive to next, so a repeated start cannot become a second path for advancing the workflow.
