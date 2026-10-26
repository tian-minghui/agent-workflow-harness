# Project namespace keyed by project name and path hash

The local control-plane home will group runs under a project namespace identified by a readable project directory name plus a short hash of its resolved absolute path. A namespace metadata file will retain the absolute project path for inspection and migration. This avoids name collisions while keeping local debugging practical and leaves a stable project identity for a future trusted control-plane service.
