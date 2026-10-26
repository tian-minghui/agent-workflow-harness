# Fixed response status set

V1.1 responses will use exactly five top-level statuses: `active`, `blocked`, `done`, `conflict`, and `error`. Gate failure is `blocked`; attempting to begin a different task while one is active is `conflict`; invalid requests, invalid control-plane state, and operational failures are `error`. This prevents gate failure, task switching, and operational failure from being collapsed into a single `failed` result.
