# Creator writes project-local workflows by default

`workflow-harness-creator` writes a new workflow to `<project>/.agents/workflows/<alias>/` unless the user explicitly asks for shared personal use. A project-local package keeps workflow YAML, gates, scripts, references, and templates together with the project and enables normal Git review and versioning. Since workflow routes often reference project files and process-specific evidence, project-local is also the safest default source scope.

The user-level catalog remains available for deliberate cross-project reuse. When the user explicitly requests a personal or cross-project workflow, the creator may write `~/.agents/workflows/<alias>/`, while respecting existing package boundaries. The built-in catalog under the harness package is not a creator destination; standard workflows enter that catalog only through the repository's normal product delivery process.
