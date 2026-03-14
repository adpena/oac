# OAC Scenarios

These scenarios demonstrate the practical application of the Open Agent Capsule toolkit in multi-agent environments.

## 1. Identity Portability (OpenClaw to Claude Code)
**Goal:** Maintain behavioral continuity across different harnesses.
- **Context:** An agent's persona and memory are developed in OpenClaw.
- **Action:** Using `oac hydrate claude-code`, the same state is projected into the Claude Code workspace.
- **Result:** The agent maintains its personality and knowledge across different vendors and execution environments.
- [View Scenario Details](./brain-transplant/README.md)

## 2. Multi-Agent Collaboration
**Goal:** Synchronize state between two different agents.
- **Context:** Agent A (e.g. Claude) proposes a new instruction via the `oac_learn` MCP tool.
- **Action:** Agent B (e.g. Gemini) reviews the proposal and promotes it to the canonical capsule.
- **Result:** Both agents now operate under the same verified rules.
- [View Scenario Details](./shared-brain/README.md)
