# Gates execute in the project directory

File-gate paths and command-gate working directories will resolve relative to the project directory, not the caller’s current working directory. After the CLI resolves the project directory, invoking `wf next` from any subdirectory produces the same gate result. This keeps the workflow control plane deterministic for coding tasks.
