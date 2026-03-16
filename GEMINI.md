# GEMINI.md

## Project Overview
**Open Agent Capsule (OAC)** is a high-signal toolkit for building and managing portable, file-first agent "brains." It treats agent state (identity, persona, rules, memory, and workflows) as a **canonical capsule** rather than a collection of ad-hoc prompt files. 

The project enables bidirectional synchronization between this canonical capsule and various native agent harness projections (e.g., Codex, Gemini, Claude Code, MCP) through a structured **Hydrate -> Work -> Ingest -> Propose -> Promote** loop.

- **Core Principles:** 
    - Files (Markdown, YAML, JSON) are the source of truth.
    - Adapters act as bidirectional compilers between capsules and native projections.
    - Learning is eval-gated and explicit; uncontrolled drift is prevented via a typed proposal/promotion flow.
    - Runtime secrets and machine-local state are never silently pulled into the capsule.

## Non-Negotiable Mandates
- **Package Management:** Always use **`uv`** for managing dependencies and virtual environments. Never use `pip` or `venv` directly.
- **Python Execution:** Always execute Python commands through the `uv` managed environment. Prefer `uv run <command>` or ensure the `.venv` created by `uv` is active.
- **Fixture Updates:** Any change to adapters or profiles MUST be followed by `uv run python scripts/update_fixtures.py` to keep regression snapshots in sync.

## Technical Stack
- **Language:** Python 3.11+
- **Package Management:** **uv**
- **Validation/Models:** Pydantic v2
- **Data Formats:** YAML (PyYAML), JSON, Markdown
- **Tooling:** Ruff (Linting/Formatting), Pytest (Testing)
- **Build System:** Maturin (pyproject.toml)

## Building and Running

### Development Setup
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Core CLI Commands (`python -m oac` or `oac`)
- `validate <path>`: Validate a capsule manifest or directory.
- `targets`: List supported agent harness targets.
- `hydrate <target> <capsule> <output>`: Generate a native projection from a capsule.
- `ingest <target> <source> <capsule>`: Scan native edits into candidate bundles.
- `propose <target> <source> <capsule>`: Turn ingest candidates into formal proposal records.
- `merge-proposals <paths...>`: Combine multiple proposal bundles and resolve conflicts.
- `conflicts <proposal>`: Show detailed collision rationale in a merged bundle.
- `workflow <proposal> <output>`: Initialize a durable promotion workflow state.
- `eval <capsule>`: Run structural and semantic eval gates.
- `promote <proposal> <capsule> --apply`: Apply a proposal to the canonical capsule.
- `revert <promotion> <capsule> --apply`: Restore backups from a prior promotion.
- `snapshot <capsule> <output> --sign-key <path>`: Create a signed, deterministic archive.
- `publish-snapshot <capsule> <output>`: Standardize a signed release into a registry layout.
- `index <capsule> <output>`: Generate a lexical keyword index.
- `structural-index <capsule> <output>`: Generate a high-level kind and tag index.
- `policy`: Show current OAC format and compatibility policies.
- `ack <target> <capsule>`: Run the Adapter Conformance Kit for a single target.
- `conformance <capsule>`: Run hydrate+ingest checks across all enabled targets.
- `serve-mcp <capsule>`: Start the OAC MCP server for record discovery.

### Validation & Testing
```bash
make check   # Run all checks (lint, test, schema, fixtures, smoke)
make test    # Run pytest suite
make lint    # Run ruff check and format check
make smoke   # Run full hydrate+ingest smoke tests across all targets
```

## Development Conventions

### Project Structure
- `src/oac/`: Core toolkit implementation (models, adapters, ingest engine).
- `examples/hello-capsule/`: The canonical reference capsule.
- `examples/adapter-profiles/`: Default configurations for supported targets.
- `docs/spec/`: Normative documentation and architecture principles.
- `tests/fixtures/`: Snapshot outputs used for regression testing of projections and ingest reports.

### Contribution Rules
1. **Definition of Done:** A change is complete only if:
    - Relevant documentation is updated.
    - The example capsule still validates.
    - Projection, ingest, and proposal fixtures are updated or still match.
    - `make check` passes.
2. **Coding Style:** Adhere to `ruff` defaults as configured in `pyproject.toml`.
3. **Architecture:** Maintain strict separation between canonical capsule state and native harness projections. Use Pydantic models for all structured data.
4. **Testing:** New features or adapter changes MUST include corresponding fixture updates in `tests/fixtures/`.
