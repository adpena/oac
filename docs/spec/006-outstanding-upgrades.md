# Outstanding upgrades

This is the condensed senior-engineer upgrade map after the starter full loop lands.

## Correctness

- stronger semantic evals beyond structural round-trips
- ownership-boundary regression tests for more edge cases
- compatibility policy for manifest, profile, and proposal schema evolution
- canonical promotion policy for target-local candidate kinds

## Performance

- incremental ingest with fingerprints and dirty-path selection
- selective hydrate by target and record scope
- derived lexical and semantic indexes
- benchmark suite for hydrate / ingest / eval cost

## Scalability

- signed releases and snapshot artifacts
- real MCP mutation surface with policy checks
- one durable workflow engine for long-running promotion flows
- multi-writer merge and sync strategy

## Adaptability and extensibility

- richer profile override semantics
- canonical hook store and runner
- wrapper packs for common harness installations
- adapter SDK helpers in Python, Rust, Go, and TypeScript

## Composability

- stable record IDs and richer provenance graph
- shared candidate / proposal diff format for tools and UIs
- local-first collaboration model once single-user correctness is harder to move
- service-pack or registry model only after signing and semantic eval work land

## The next best step

Tighten the eval gate and signing path before adding more harness surface area.
