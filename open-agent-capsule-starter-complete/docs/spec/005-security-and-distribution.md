# Security and distribution

## Security boundaries

Never treat these as canonical by default:

- secrets
- auth tokens
- sessions
- provider caches
- machine-local state
- browser-local state

## Distribution direction

The starter now implements **deterministic local snapshots with checksums**.
It still does **not** implement signing or remote publication.

The intended direction remains:

- signed snapshots
- explicit compatibility policy
- portable source bundle first
- optional sidecars for runtime or learned artifacts
- candidate bundles kept distinct from promoted canonical state

## Open-source launch posture

Launch honestly:

- say what is real
- say what is starter-only
- say what is next
- do not claim semantic eval, collaborative merge, mutation, or registry support before they exist
