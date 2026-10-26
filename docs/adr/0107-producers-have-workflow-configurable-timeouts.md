# Producers have workflow-configurable timeouts

A condition producer runs synchronously while the control plane selects a route. Its default execution-time budget is 30 seconds, and a workflow definition may declare a timeout override. This allows a workflow to account for a legitimately heavier bounded evidence check while retaining the default contract for simple producers.

Exceeding the configured budget terminates the producer and returns an operational `error`. A timeout is never normalized to `false` and never advances or changes authoritative state. The timeout is not a model-facing field; the route response exposes only the existing error status and bounded reason.

The default budget is 30 seconds. A workflow may declare a single bounded override in the workflow definition; the exact field shape is part of the v2 schema. A timeout always terminates the producer process and returns an operational `error` without changing authoritative state.

Workflow v2 exposes one top-level `producer_timeout_seconds` integer. The default value is 30, and static validation accepts only integers from 1 to 300. The value applies to every `workflow_script` and `command` condition producer in that workflow; producers do not have individual timeout fields. The field is deliberately uniform so one route evaluation has one predictable budget, rather than combining script-specific budgets in the same graph.
