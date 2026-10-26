# Human reasons use a fixed single-line template

Pending, rejected, stale-approval, and unchanged-after-rejection responses generate `blocked.check.reason` from fixed control-plane templates. The YAML request remains authoritative content, but whitespace is normalized to a single line; evidence paths preserve their declaration order and the template appends the concrete decision commands. Workflow validation limits the request and evidence set so the generated reason does not require runtime truncation.
