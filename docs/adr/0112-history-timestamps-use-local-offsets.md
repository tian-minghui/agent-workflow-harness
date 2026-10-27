# History timestamps use local ISO-8601 offsets

## Status

Accepted

## Context

`history.jsonl` is a project-local, human-inspectable audit log. ADR-0037 originally normalized each event timestamp to UTC and used the `Z` suffix. That representation is machine-friendly, but it displays a wall-clock time that can differ by several hours from the machine's local time, which makes a local operator question whether the timestamp is stale or incorrect.

## Decision

New history events record timestamps in the event host's local timezone using ISO-8601 with an explicit numeric offset—for example, `2026-10-27T14:34:29.766+08:00` in Asia/Shanghai or `2026-10-27T06:34:29.766+00:00` on a UTC host. The harness does not hardcode a timezone and does not store a second localized timestamp field.

## Consequences

The raw history file shows wall-clock time that matches the local operator's clock while the numeric offset keeps it unambiguous and machine-parsable. Consumers must parse the ISO-8601 value before comparing or sorting timestamps; they must not compare raw strings from different offsets. Existing records, including UTC `Z` records, remain valid audit facts and are not rewritten.

This supersedes the UTC-normalized timestamp format in ADR-0037 without changing UTF-8 human-readable serialization, append-only behavior, or the decision not to invent timestamps for legacy records.
