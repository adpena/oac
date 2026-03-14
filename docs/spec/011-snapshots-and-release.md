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
- asymmetric SSH signatures
- standardized registry layouts

## Snapshot trust

### Polymorphic signing

Snapshots support two signing modes via the `--sign-key` flag:
1. **Symmetric (HMAC-SHA256):** Using a raw secret string.
2. **Asymmetric (SSH-Ed25519):** Using a standard OpenSSH private key. Uses `ssh-keygen` for verifiable signatures.

The `signature_kind` is stored in the snapshot metadata.

## Distribution

### Registry layout

The `publish-snapshot` command standardizes the organization of releases:
```text
<publish_root>/
  <capsule_id>/
    <snapshot_id>/
      snapshot.json
      checksums.json
      <snapshot_id>.tar.gz
      signature.sig
```
This layout is designed to be served by any static HTTP server or S3 bucket.

## What still remains

- OCI packaging or registry publication
- release automation and changelog discipline
