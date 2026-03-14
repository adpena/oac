# Scenario: Multi-Agent Collaboration

This scenario demonstrates how multiple agents using different harnesses (e.g. **Claude Code** and **Gemini CLI**) can synchronize their operating state via a shared **Open Agent Capsule**.

## Setup

1. **Agent A (Claude Code):** Operating in `./claude-env`.
2. **Agent B (Gemini CLI):** Operating in `./gemini-env`.
3. **The Shared State:** A local OAC Capsule directory.

## Execution

### 1. State Projection
Hydrate the capsule for both targets:
```bash
oac hydrate claude-code examples/hello-capsule ./claude-env
oac hydrate gemini examples/hello-capsule ./gemini-env
```

### 2. Native Edit (Claude Code)
Give Claude a new project rule (e.g. "Only use Vanilla CSS"). Claude writes this to its native `.oac/claude/project-guidance.md`.

### 3. Pipeline Orchestration (Claude Code)
Instruct Claude to propose the change to the shared capsule. Claude calls the `oac_learn` tool via the OAC MCP server. This automates the ingest, proposal generation, and structural evaluation.

### 4. Review and Promotion (Gemini CLI)
Switch to the Gemini environment. Instruct Gemini to find the latest proposal, review the structured diff, and promote it. Gemini calls `oac_promote` via the MCP server.

## Results

- **Verified Truth:** The new rule is now stored in the canonical capsule as a standard Markdown file.
- **Automated Sync:** Running `oac hydrate` again ensures both agents are now operating under the same verified instruction set.
- **Interoperability:** Different agents synchronized their internal logic using a shared, vendor-neutral protocol and format.
