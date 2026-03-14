# Open Agent Capsule (OAC)

[![CI](https://github.com/adpena/oac/actions/workflows/ci.yml/badge.svg)](https://github.com/adpena/oac/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A file-first specification and toolkit for managing agent state as a versioned, portable canonical artifact. Identity, persona, procedures, and memory live in plain files — not trapped in proprietary harness configurations or model-specific blobs.

## System Goals

As agentic systems become foundational infrastructure, maintaining a verifiable and portable state is a technical requirement. OAC separates the agent's durable intelligence from its specific execution harness.

- **Harness Portability:** Standardized state allows agents to be moved between model providers and execution tools without manual reconfiguration.
- **Verified State:** Every change to the canonical state must pass structural evaluation gates and be cryptographically signed before promotion.
- **Context Efficiency:** Targeted record selection reduces data processing costs and improves response accuracy by pruning noise from the context window.
- **Discovery Surface:** Includes a Model Context Protocol (MCP) server for record discovery and autonomous pipeline management.

## Operational Status

OAC is implemented for the following targets:

- **Codex:** Repository-native instructions.
- **Claude Code:** High-speed execution and auto-memory.
- **OpenClaw:** High-fidelity persona and memory.
- **Gemini CLI:** Multi-surface instructions.
- **OpenCode:** Generic project surfaces.
- **MCP / WebMCP:** Discovery and bridge protocols.

## Quick Start

```bash
# Requires Python 3.11+ and a Rust toolchain
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

oac targets                                    # list supported harnesses
oac validate examples/hello-capsule            # verify a capsule
oac hydrate claude-code examples/hello-capsule ./workspace  # project to Claude Code
```

## Core Loop

```bash
# 1. Project the capsule for a target
oac hydrate claude-code examples/hello-capsule ./workspace

# 2. Scan native edits into typed candidates
oac ingest claude-code ./workspace examples/hello-capsule

# 3. Turn candidates into a reviewable proposal
oac propose claude-code ./workspace examples/hello-capsule

# 4. Apply the proposal to the canonical files
oac promote <proposal-path> examples/hello-capsule --apply

# 5. Release a signed snapshot
oac snapshot examples/hello-capsule ./releases --sign-key ~/.ssh/id_ed25519
```

## Documentation

- [Project Rationale](docs/RATIONALE.md)
- [Business Case](docs/BUSINESS_CASE.md)
- [Usage Scenarios](examples/scenarios/README.md)
- [Normative Specifications](docs/spec/README.md)
