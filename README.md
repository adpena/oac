# Open Agent Capsule (OAC)

OAC is a file-first specification and toolkit for managing agent state (identity, persona, procedures, and memory) as a versioned, portable canonical artifact. It addresses the challenge of agent state being trapped in proprietary harness configurations or model-specific blobs.

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

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
make check
```

## Functional Core

```bash
# 1. Project the capsule for a target
oac hydrate claude-code examples/hello-capsule ./workspace

# 2. Ingest edits and generate a verified proposal
oac learn claude-code ./workspace examples/hello-capsule

# 3. Apply the proposal to the canonical files
oac promote <proposal-path> examples/hello-capsule --apply

# 4. Release a signed snapshot
oac snapshot examples/hello-capsule ./releases --sign-key ~/.ssh/id_ed25519
```

## Documentation

- [Project Rationale](docs/RATIONALE.md)
- [Usage Scenarios](examples/scenarios/README.md)
- [Normative Specifications](docs/spec/README.md)
- [Project Homepage](index.html)
