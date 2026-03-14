# Roadmap

## Gate model

Every gate should end in a working artifact, a tighter contract, and passing tests.

## Gates

### G0 — Canonical format
Status: done

- manifest schema exists
- example capsule validates
- canonical tree shape is documented

### G1 — Adapter profile contract
Status: done

- adapter profile schema exists
- bundled profiles validate
- profiles can be scaffolded and customized

### G2 — Real launch projections
Status: done

- `oac hydrate` renders launch targets
- snapshot fixtures match generated output
- profile path overrides affect emitted surfaces

### G3 — Starter ingest paths
Status: done

- Codex, OpenClaw, Claude Code, OpenCode, and Gemini can be scanned back into typed candidate reports
- MCP and WebMCP report an explicit read-only ingest posture
- ingest respects profile path overrides
- ingest output is deterministic enough for snapshot tests

### G4 — Typed proposal and promotion flow
Status: done

- ingest candidates become explicit proposal records
- promotion is reviewable and reversible
- provenance attaches to candidate and promotion outputs
- candidate bundles diff cleanly against current canonical files

### G5 — Eval gate
Status: starter-done

- promotion requires passing a deterministic structural eval slice
- regression fixtures exist for supported targets
- round-trip changes can be rejected before canonical write-back

### G6 — Distribution and trust
Status: starter-done

- deterministic local capsule snapshot format exists
- checksums are emitted
- release and signing policy are still future work

### G7 — Scale and collaboration
Status: starter-done

- conformance command exercises hydrate + ingest across enabled targets
- richer sync, merge, and mutation surfaces remain future work
- benchmark automation remains future work

## Current instruction

Do not skip semantic eval work in order to add more surface area.
The next highest-leverage step is improving the eval gate and signing path without breaking the current review seam.
