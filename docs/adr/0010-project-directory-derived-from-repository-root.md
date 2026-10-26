# Project directory derived from the repository root

The workflow runtime will determine the project directory by first accepting an operator-set `WF_PROJECT_DIR` override, then using the Git repository root, and finally falling back to the current directory outside a repository. The agent-facing CLI has no project-directory argument. This lets coding tasks in any subdirectory map to one stable project namespace while remaining usable for non-Git projects.
