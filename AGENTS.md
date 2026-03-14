# AGENTS.md

This repository is a Codex-first starter for **Open Agent Capsule**.

## Operating rules

- Use **uv** for all package management.
- Keep the canonical layer file-first and human-readable.
- Prefer deterministic, reversible changes.
- Move one clear gate at a time.
- Do not add infrastructure before the current gate needs it.
- Keep generated fixtures, docs, and code in sync.
- Be explicit about what is implemented versus scaffolded.
- Treat ingest as candidate generation, not automatic promotion.
- Treat proposal records as the review seam, not as a formality.

## Read first

1. `README.md`
2. `ROADMAP.md`
3. `docs/spec/000-principles.md`
4. `docs/spec/001-canonical-format.md`
5. `docs/spec/002-adapter-model.md`
6. `docs/spec/004-learning-loop.md`
7. `docs/spec/009-proposal-and-promotion.md`

Then read the most relevant target spec before changing an adapter.

## Preferred work pattern

1. Identify the next incomplete gate in `ROADMAP.md`.
2. Choose the smallest vertical slice that moves it.
3. Update code, docs, tests, and fixtures in one change.
4. Run the smallest meaningful check first.
5. Finish with `make check`.

## Change boundaries

Do:

- tighten schemas
- improve adapter clarity
- keep profiles, ingest plans, proposal mappings, and fixtures aligned
- add tests before widening scope
- prune ambiguity

Do not:

- silently change canonical semantics
- move secrets or runtime state into the shared capsule
- bury durable rules in one-off prompts
- skip candidate review and call it learning
- turn the starter into a speculative platform rewrite

## Current priority order

- semantic eval slices
- snapshot signing and release policy
- multi-writer merge boundaries
- MCP mutation surface
- benchmark automation

## When editing fixtures

Projection fixtures under `tests/fixtures/projections/`, ingest fixtures under `tests/fixtures/ingest/`, and proposal fixtures under `tests/fixtures/proposals/` are snapshots of actual generated output. Regenerate them with:

```bash
python scripts/update_fixtures.py
```

Do not hand-edit them unless you also understand the renderer, ingest-plan change, or proposal-mapping change that caused the drift.
