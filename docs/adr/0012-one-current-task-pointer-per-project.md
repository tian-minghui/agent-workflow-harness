# One current-task pointer per project namespace

V1.1 will use a single control-plane pointer in a project namespace to identify the active control-plane instance. The CLI resolves the project from the current working directory, so its model-facing commands no longer require --task-dir. A project has one active workflow run at a time; future versions may add explicit task selection rather than reintroducing task directories.
