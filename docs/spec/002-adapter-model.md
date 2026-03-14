# Adapter model

## Adapter responsibilities

Each adapter owns four things:

- mapping canonical records into native target surfaces
- declaring lossiness and ownership boundaries
- declaring a target-local ingest plan
- eventually ingesting native edits back into typed candidates

## Ownership modes

- `managed-file` — OAC owns the whole file
- `managed-section` — OAC owns a marked region inside a larger file
- `imported-file` — the harness points at an OAC-generated file
- `sidecar` — useful nearby data that is not canonical

## Portability classes

- `portable` — safe to travel with the capsule
- `user-local` — useful but normally machine- or user-local
- `runtime-state` — auth, sessions, secrets, caches, and similar host-owned state

## Adapter profiles

A profile is the customization layer for a target. It can override:

- output paths
- surface names
- hooks
- wrappers
- target-local flags

The profile should not change canonical meaning. It changes *projection shape*, not *source semantics*.

Custom profiles provided via `--profile` are **surgically merged** with the target's default profile using keyed merging (by `name` or `canonical_kind`).

## Hydration process

Hydration is an optimized deterministic render pass.
The `write_if_changed` logic ensures that only modified content is written to the destination, preserving file timestamps and minimizing I/O. Selective hydration via `--kind` allows for partial updates of specific record types.

## Ingest plans

A starter ingest plan declares:

- which native paths are scanned
- which candidate kind each path produces
- ownership mode and portability class
- which parser is used
- where the candidate bundle would land

That keeps ingest declarative, profile-aware, and testable.

## Hooks and wrappers

Hooks and wrappers are opt-in escape hatches for advanced users.
They are useful for:

- post-hydrate indexing
- local launcher wrappers
- notifications
- custom ingest cleanup

They are not a replacement for the canonical model.
