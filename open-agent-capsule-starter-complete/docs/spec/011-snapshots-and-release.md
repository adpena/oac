# Snapshots and release

## Starter snapshot contract

`oac snapshot` creates:

- a deterministic `tar.gz` archive of the capsule
- a checksum manifest for included files
- a small snapshot metadata document

The snapshot id is content-derived rather than time-derived.

## Exclusions

The starter excludes local promotion and prior snapshot directories so the snapshot remains focused on the shareable capsule rather than local operational history.

## Why this is enough for now

The project needs a real distribution seam early, but it does not need to fake a mature registry before the core loop is solid.
Checksums and deterministic packaging are enough to unblock:

- reproducible local exports
- fixture-based release tests
- later signing and registry work

## What still remains

- signing
- OCI packaging or registry publication
- compatibility window policy
- release automation and changelog discipline
