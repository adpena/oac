# Ingest support matrix

## Partial starter ingest

These targets support starter ingest today:

- Codex
- OpenClaw
- Claude Code
- OpenCode
- Gemini CLI

Starter ingest means:

- scan only declared native surfaces
- return deterministic typed candidates
- respect adapter profile path overrides
- avoid runtime-state capture
- stop before proposal or promotion

## Read-only targets

These targets are intentionally read-only in the starter:

- MCP
- WebMCP

That means the repo can still hydrate companion resources for them, but ingest reports an explicit read-only posture.

## Promotion nuance

A target-native candidate kind does not automatically imply a canonical record kind.
Examples:

- `behavior.rule` often promotes into shared guidance
- `memory.semantic` often promotes into canonical memory
- `memory.index` may stay local
- `agent.specialist`, `command.template`, `hook.logic`, and `config.signal` may stay target-local unless explicitly abstracted
