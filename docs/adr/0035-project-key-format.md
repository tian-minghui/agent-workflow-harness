# Project key format

A project namespace is `<project-name-slug>--<sha256-path-16>`. The display slug is derived from the project directory basename, made filesystem-safe, limited to 40 characters, and may contain Unicode. The identity suffix is the first 16 lowercase hexadecimal characters of the SHA-256 digest of the resolved project path. The namespace metadata records the full resolved project path for inspection; automatic rebinding after a project move remains a future extension.
