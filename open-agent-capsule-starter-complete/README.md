# Open Agent Capsule Starter

A high-signal starter repo for building **Open Agent Capsule (OAC)**: one canonical, file-first agent brain with native projections, typed ingest, explicit proposals, a structural eval gate, reversible promotion, and deterministic local snapshots.

## The point

Most serious agent setups eventually accumulate the same kinds of state:

- durable rules
- identity and persona
- user model
- curated memory
- repeatable workflows
- harness-specific wiring
- target-local extras that should be reviewable without automatically becoming canonical

This project treats that state as a **portable capsule** instead of a pile of ad hoc prompt files.

## Design rules

- Canonical source stays in files.
- Markdown/YAML/JSON are the source of truth.
- Native harness projections are generated, reviewable artifacts.
- Ingest produces **typed candidate bundles**, not blind write-back.
- Proposals make destination, rationale, diff, and reversibility explicit.
- Promotion runs through an eval gate before canonical write-back.
- Snapshots are deterministic local artifacts with checksums.
- Runtime state, auth, and secrets are not silently pulled into the capsule.

## What is implemented in this starter

Implemented now:

- manifest schema and validator
- adapter profile schema and validator
- bundled default profiles for launch targets
- a real `hydrate` command for the launch targets
- starter `ingest` paths for the file-based local harness targets
- read-only ingest posture for MCP and WebMCP
- snapshot fixtures for generated projections
- snapshot fixtures for ingest candidate reports
- snapshot fixtures for proposal bundles
- typed `propose` flow with canonical destination mapping and diffs
- structural `eval` and `conformance` passes
- reversible `promote` and `revert` flow with backups
- deterministic local `snapshot` packaging with checksums
- a canonical example capsule
- polyglot hook examples for Python, TypeScript, Go, Rust, Zig, and WASM
- MCP/WebMCP bridge sketches
- Codex-friendly repo instructions and prompts
- Linear seed artifacts

Still intentionally starter-sized:

- semantic evals and learned scoring
- signed registry publishing
- durable workflow engine
- real MCP mutation surface
- conflict-aware multi-writer sync
- benchmark automation

## Repo map

- `src/oac/` — CLI, models, profiles, adapters, ingest engine, proposals, evals, and snapshots
- `examples/hello-capsule/` — canonical demo capsule
- `examples/adapter-profiles/` — bundled default profiles per target
- `examples/hooks/` — canonical hook contract examples in multiple runtimes
- `examples/bridges/` — MCP and WebMCP bridge sketches
- `tests/fixtures/projections/` — snapshot outputs for each launch target
- `tests/fixtures/ingest/` — snapshot ingest reports for each launch target
- `tests/fixtures/proposals/` — snapshot proposal bundles for each launch target
- `docs/spec/` — small set of normative docs
- `prompts/` — Codex bootstrap prompts
- `linear/` — seed backlog artifacts

## First hour

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make check
```

Then inspect the starter from the CLI:

```bash
python -m oac validate examples/hello-capsule
python -m oac targets --verbose
python -m oac describe-target codex
python -m oac describe-ingest codex
python -m oac hydrate codex examples/hello-capsule /tmp/oac-codex
python -m oac ingest codex /tmp/oac-codex examples/hello-capsule --json
python -m oac propose codex /tmp/oac-codex examples/hello-capsule --json
python -m oac eval examples/hello-capsule
python -m oac conformance examples/hello-capsule
python -m oac snapshot examples/hello-capsule /tmp/oac-snapshots
```

To adapt a target to your real environment:

```bash
python -m oac scaffold-profile codex examples/adapter-profiles/codex.example.test.yaml
python -m oac hydrate codex examples/hello-capsule /tmp/oac-codex --profile examples/adapter-profiles/codex.example.test.yaml
python -m oac ingest codex /tmp/oac-codex examples/hello-capsule --profile examples/adapter-profiles/codex.example.test.yaml --json
python -m oac propose codex /tmp/oac-codex examples/hello-capsule --profile examples/adapter-profiles/codex.example.test.yaml --output /tmp/codex-proposal.json
python -m oac promote /tmp/codex-proposal.json examples/hello-capsule
```

## The loop

```text
hydrate -> work natively -> ingest -> candidate bundle -> propose -> eval -> promote -> snapshot
```

The starter stops short of uncontrolled learning. It insists on typed candidates, explicit proposal records, a structural eval gate, and reversible promotion.

## Recommended defaults

- project name: **Open Agent Capsule**
- CLI/package shorthand: **`oac`**
- control plane: Python + Pydantic
- compiled helpers: Rust, Go, Zig, or WASM when justified
- bridge surfaces: MCP and WebMCP
- source-of-truth rule: files before databases
- learning rule: candidates before proposals, proposals before promotion

## Definition of done for every meaningful change

A change is not done until:

- the relevant doc is updated
- the example capsule still validates
- projection fixtures still match generated output, or are intentionally updated
- ingest fixtures still match generated output, or are intentionally updated
- proposal fixtures still match generated output, or are intentionally updated
- automated tests cover the behavior
- `make check` passes

## Where the ambition goes next

The next serious milestone is not more adapter sprawl. It is:

1. stronger semantic evals
2. signed release artifacts
3. mutation-safe collaboration
4. benchmark and conformance hardening

That is the shortest path from a promising starter to a real portable cognition system.
