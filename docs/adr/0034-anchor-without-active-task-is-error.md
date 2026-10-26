# Anchor without an active task is an error

If the repository task anchor exists but the current project namespace has no active control-plane task, `start` and `next` will return an error instead of silently deleting the anchor or starting a new task. This prevents a project directory move from silently orphaning an active task under the previous path-derived namespace. Automatic rebinding or migration across project namespaces is deferred to a later version.
