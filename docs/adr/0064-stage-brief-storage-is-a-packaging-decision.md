# Stage brief storage is a packaging decision

Status: Superseded by ADR 0066

A stage guide is source material for the active stage, not a required file format or runtime-managed resource bundle. A workflow may keep guidance inline in YAML or in package files. The harness remains responsible only for returning the active guide after `${workflowDir}` substitution, not for hiding or compiling package assets.