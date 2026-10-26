# PRD-to-Spec routing is the v2 acceptance fixture

The v2 conditional-routing release uses a deterministic `prd-to-spec-routing` acceptance workflow before migrating the complete PRD-to-Spec business flow. The fixture models three routing capabilities that the real process needs: `entry_mode == existing_prd|confirmed_prd` selects between full PRD clarification and direct architecture continuation, `technical_contract_required == true|false` chooses between technical-contract clarification and Spec task assembly, and `routing_gap == true|false` chooses between the normal path and an explicit backedge to architecture.

The fixture proves the control-plane mechanism: step-local candidate edges, exact string and boolean comparisons, `wf start --var`, lazy fact producers, runtime refresh, default edges, backedge selection, route audit records, and the fixed backedge cycle limit. It does not attempt to recreate Dima access, Yuque delivery, multi-Bot dependency ordering, coding work-item creation, or full human artifact confirmation.

Migrating the complete `prd-to-spec` workflow is deferred to a later business-migration release. This keeps the v2 harness iteration focused on routing correctness while using PRD-to-Spec as a realistic set of acceptance scenarios rather than a synthetic toy graph.
