# Transitions are step-local

A workflow stores outbound routes directly under the step that owns them. A source step therefore contains its guide, gates, optional fact producers, and its complete list of candidate outgoing transitions. A step-local transition names only `to` and optionally `when` or `default`; it does not repeat the source step as `from`, and a workflow does not maintain a separate global transition list for these candidate edges.

Keeping routes with their source step makes conditional routing cohesive: the step declares how a fact such as `technical_contract_required` is produced and which edges consume it. It also makes graph validation local: a step with multiple candidate edges can be checked for at most one default, exact `when` arbitration, and a valid target in the same declaration block. A backedge is simply a `to` value that names an earlier step and remains subject to the fixed cycle limit.

Moving conditional transitions into a global list would recreate the fragmented author-ind model where producers belong to one step while their consuming edges belong to another. The top-level workflow retains global identity only: `entry`, `terminal`, and the complete `steps` mapping.
