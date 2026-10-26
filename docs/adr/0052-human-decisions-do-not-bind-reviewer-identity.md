# Human decisions do not bind reviewer identity in v1.2

V1.2 records every approval and rejection as a local control-plane decision without a trusted reviewer identity field. A shell account, local user name, or manually supplied reviewer name would be self-reported and would add false trust to the local audit. Reviewer context may be captured in an approval note, but only a future trusted approval service can make identity a security property.
