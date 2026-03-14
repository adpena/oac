# Contributing

Thanks for contributing.

## Before you open a PR

- read `README.md`
- read `AGENTS.md`
- read `ROADMAP.md`
- run `make check`

## Change expectations

Keep changes narrow.
If a change affects canonical semantics, adapter behavior, or fixtures, update the relevant docs in the same PR.

## Snapshot fixtures

If a renderer changes, regenerate fixtures with:

```bash
python scripts/update_fixtures.py
```

## Honesty policy

Do not describe starter scaffolding as complete production support.
