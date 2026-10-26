# Acceptance fixtures live in test assets

The `prd-to-spec-routing` v2 acceptance workflow is stored as a test fixture, not as a built-in workflow package. Its source location is under the repository test assets; integration tests copy it into a temporary project's `.agents/workflows/<alias>/` directory when the catalog must resolve the alias.

This placement preserves the distinction between production workflows and capability tests. The fixture is intentionally synthetic and can be modified across cases to force a false producer result or a third backedge violation. Exposing it as a built-in alias would imply that it is a user-ready workflow and would add a non-production entry to the runtime catalog.

A complete, production-ready `prd-to-spec` workflow can later enter the built-in catalog through a separate migration release that provides the full business guide, gates, references, and integration tests.
