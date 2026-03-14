# Proposal and promotion

## Why proposals exist

Ingest tells you **what changed natively**.
A proposal tells you **whether it should become canonical, where it would land, why that mapping is valid, and how it differs from the current file**.

That makes proposals the review seam.

## Proposal record shape

Every record in a proposal bundle includes:

- source candidate id
- target harness
- native source path and surface name
- candidate kind and resolved canonical kind
- disposition (`promotable`, `noop`, `deferred`, `user-local`, `runtime-state`, `unsupported`)
- planned operation (`create`, `update`, `skip`)
- canonical destination path when one exists
- rationale for the mapping
- candidate content
- canonicalized content
- current canonical content
- unified diff
- **structured diff metrics** (additions, deletions, total lines)
- provenance metadata copied from ingest

## Starter mapping policy

The starter keeps the mapping policy opinionated and narrow:

- `behavior.rule` -> `procedures/behavior/`
- `memory.semantic` -> `memory/semantic/`
- skill-like `procedure.workflow` -> `skills/<name>/SKILL.md`
- non-skill `procedure.workflow` -> `procedures/workflows/`
- `agent.specialist` -> `procedures/agents/`
- `command.template` -> `procedures/commands/`
- `config.signal` -> `procedures/config/<target>/`
- `hook.logic` -> `procedures/hooks/<target>/`
- user-local or runtime-state records -> never auto-promoted

## Promotion policy

Promotion in the starter is intentionally conservative:

- only `promotable` records can write
- promotion runs after the eval gate unless the operator explicitly skips it
- updated files are backed up under `.oac/promotions/<promotion-id>/backups/`
- the proposal bundle and promotion report are stored alongside the backups
- revert uses those backups or deletes files that were created by the promotion

## Advanced review features

### Structured diffs

Every proposal record includes a `structured_diff` object. This allows external tools and UIs to render rich diff views (line counts, heatmaps) without re-parsing raw unified diff text.

### Multi-bundle merging

The `merge-proposals` command allows combining edits from multiple sources into a single reviewable bundle. It supports explicit conflict resolution policies: `ours`, `theirs`, and `fail`.

## What this does not solve yet

- collaborative approval or review UI
- remote publication of proposal or promotion artifacts
