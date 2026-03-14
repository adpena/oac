You are working inside the Open Agent Capsule starter repository.

Read these files first, in order:

1. `README.md`
2. `AGENTS.md`
3. `ROADMAP.md`
4. `docs/spec/000-principles.md`
5. `docs/spec/001-canonical-format.md`
6. `docs/spec/002-adapter-model.md`
7. `docs/spec/004-learning-loop.md`
8. `docs/spec/009-proposal-and-promotion.md`

Then do this:

1. Identify the next incomplete or starter-level gate in `ROADMAP.md`.
2. Pick the smallest complete change that moves it.
3. Implement it end to end.
4. Update docs, tests, and fixtures in the same change.
5. Run the relevant checks.
6. End with:
   - gate moved
   - files changed
   - next smallest slice

Constraints:

- Do not broaden scope without a gate-level reason.
- Keep the canonical layer file-first.
- Treat ingest output as candidate generation, not automatic promotion.
- Treat proposal records as the review seam.
- Be explicit about what is implemented versus scaffolded.
- Prefer deterministic tests over new complexity.
