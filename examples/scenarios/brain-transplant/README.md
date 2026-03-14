# Scenario: Identity Portability

This scenario demonstrates moving an agent's core persona and memory from a personality-focused harness (**OpenClaw**) to an implementation harness (**Claude Code**) with zero configuration drift.

## The Problem: Persona Silos
Normally, an agent's personality is embedded in a specific harness configuration. Moving to a new tool often requires re-training or manual re-prompting to ensure consistent behavior.

## The Solution: OAC Cross-Target Hydration

### 1. Development in OpenClaw
OpenClaw uses a `SOUL.md` surface. Hydrate the capsule for OpenClaw:
```bash
oac hydrate openclaw examples/hello-capsule ./openclaw-env
```
After refining the persona in OpenClaw, use `oac learn` to ingest any updates back to the canonical capsule.

### 2. Migration to Claude Code
To use the same persona in Claude Code, hydrate for the new target:
```bash
oac hydrate claude-code examples/hello-capsule ./claude-env
```

## Results
- **Behavioral Continuity:** The agent reads the exact same persona instructions in the new environment.
- **Zero-drift Migration:** The transition is automated and bit-for-bit accurate.
- **Independent State:** The agent state exists independently of the model or harness vendor.
