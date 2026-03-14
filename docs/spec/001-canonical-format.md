# Canonical format

## Canonical tree

```text
capsule/
  manifest.yaml
  identity/
    identity.md
    persona.md
    user-model.md
  memory/
    semantic/
      *.memory.md
  procedures/
    *.memory.md
  skills/
    <skill>/SKILL.md
  provenance/
    sources.jsonl
```

## Canonical record kinds in the starter

- `identity.display`
- `identity.persona`
- `user.model`
- `memory.semantic`
- `procedure.workflow`

The starter stays intentionally narrow on the canonical side.
Ingest may discover richer target-native candidate kinds before promotion decides how they map back.

## Candidate bundle direction

Starter ingest reports suggest bundle paths like:

```text
.oac/candidates/<target>/...
```

Those candidate bundles are **not canonical yet**.
They are the review boundary between native edits and shared durable knowledge.

## Derived artifacts

These are not canonical:

- **lexical and structural indexes** (`oac index` and `oac structural-index`)
- vector indexes
- caches
- SQL or analytics tables
- projection metadata
- harness config sidecars
- runtime state sidecars
- learned deltas or adapters
- candidate bundles awaiting promotion

Those artifacts may be useful, but they must be rebuildable or separately governed.
