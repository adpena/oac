# Target mappings

## Codex

- rules -> `AGENTS.md`
- workflows -> `.agents/skills/*`
- ingest posture -> scan managed rule region plus skill bundles

## OpenClaw

- rules -> `AGENTS.md`
- persona -> `SOUL.md`
- user model -> `USER.md`
- identity -> `IDENTITY.md`
- curated memory -> `MEMORY.md`
- episodic notes -> `memory/YYYY-MM-DD.md`
- workflows -> `skills/*`
- ingest posture -> scan portable workspace surfaces, ignore runtime state sidecars

## Claude Code

- shared guidance -> `CLAUDE.md` or imported OAC guidance file
- local auto-memory index -> `memory/MEMORY.md`
- detailed local memory -> `memory/*.md`
- ingest posture -> scan guidance and memory topics, mark memory as user-local
- rule: `MEMORY.md` is an index, not a dump

## OpenCode

- shared rules -> `AGENTS.md`
- workflows -> `.agents/skills/*`
- specialist agents -> `.opencode/agents/*`
- repetitive commands -> `.opencode/commands/*`
- advanced callbacks -> `.opencode/plugins/*`
- ingest posture -> scan target-local command, agent, plugin, and config signal too

## Gemini CLI

- root context -> `GEMINI.md`
- imported depth -> `.oac/gemini/instructions/*`
- specialist agents -> `.gemini/agents/*`
- settings/MCP wiring -> `.gemini/settings.json`
- optional hook bundles -> `.gemini/extensions/oac/*`
- ingest posture -> scan root context, imports, agents, settings, and extension assets

## MCP and WebMCP

Treat both as access surfaces, not canonical storage.
The launch shape is read-only, and ingest is explicitly read-only as well.
