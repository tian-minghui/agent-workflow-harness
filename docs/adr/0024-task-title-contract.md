# Task title contract

A task title is required and must be a single natural English line of 5–120 characters. It may contain only ASCII letters, digits, spaces, and hyphens, and must contain at least one alphanumeric character so the derived task slug is never empty.

The CLI trims leading and trailing whitespace and collapses internal whitespace before storing the title and comparing it exactly. Exact normalized matching remains the only resume rule; approximate or semantic matching is not used.

The title is not a directory-name format. The control plane derives a bounded, lowercase slug from a natural title such as `Implement user profile export`; the title itself never needs to be written as `implement-user-profile-export`.
