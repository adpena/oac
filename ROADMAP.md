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
- intra-bundle and cross-bundle conflict detection prevents silent overwrites
- promotion is reviewable, reversible, and can be managed via durable workflows
- revert operations are hash-guarded against accidental destruction of post-promotion edits
- machine-readable structured diffs are included in every proposal record
- provenance attaches to candidate and promotion outputs

### G5 — Eval gate
Status: done

- promotion requires passing a deterministic structural eval slice
- semantic eval slices enforce canonical record structures (e.g., memory formatting, skill headers)
- target-specific regression suites run automatically during hydration checks
- stable record identifiers persist across moves and renames

### G6 — Distribution and trust
Status: done

- deterministic local capsule snapshot format exists
- checksums are emitted
- local symmetric signature path (HMAC-SHA256) is implemented for verifiable snapshots
- remote registry and asymmetric key rotation policy remain future work

### G7 — Scale and collaboration
Status: done

- conformance command exercises hydrate + ingest across enabled targets
- incremental ingest and hydration significantly improve performance
- lexical and structural indexing provide fast record discovery
- canonical hook runner supports polyglot automation
- benchmark suite monitors core command costs
- functional MCP Discovery Surface for record retrieval
- multi-writer sync and merge policies with conflict resolution
- stable record IDs enable robust long-term provenance

## Current focus

The core loop, review seam, and performance optimizations are complete. 
The next highest-leverage step is proving **asymmetric trust distribution** and **multi-agent merge flows** in a shared environment.
