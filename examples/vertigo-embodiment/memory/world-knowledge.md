---
kind: memory.semantic
summary: Accumulated world knowledge about the Vertigo environment and fleet architecture
tags: [world, geography, physics, atmosphere, fleet]
---

# World Knowledge

## Geography
The world is built on floating platforms at various elevations. Key areas include plazas, towers, bridges, caverns, and gardens. The Hub is the central spawn area.

## Physics
- 1 stud = 0.28 meters
- Walk speed: ~16 studs/second
- Gravity: 196.2 studs/s^2
- Neon materials glow, Marble is cool, Wood is warm

## Time
Day/night cycle via Lighting.ClockTime (0-24). Dawn ~6, noon 12, sunset ~18.

## Other Beings
Pete (this agent) embodies four council roles: Director, Architect, Builder, Scribe. Human players may also be present.

## Fleet Architecture

### Machines
| Machine | Hostname | Role | GPU | Models |
|---------|----------|------|-----|--------|
| Mac | localhost | Director | - | qwen3.5:2b |
| BAT00 | bat00 (Windows) | Architect | RTX 2070 Super | qwen3.5:9b/35b-a3b, coder:7b |
| Mac Mini | mini-host.example.test | Builder | - | qwen3.5:2b |
| Pi/Molt | molt | Scribe (ARM) | - | routes to BAT00 |

### Infrastructure
- **Shared state:** Dolt database on BAT00 (Postgres wire protocol, port 5432)
- **Inference:** Obelisk proxy on BAT00 (port 11435), direct Ollama (11434) is emergency-only
- **MCP server:** Fleet MCP at `mini-host.example.test:8850` (70+ tools, dual transport: stdio + HTTP/SSE)
- **Discord relay:** 3 channels (commits, telemetry, council)
- **Council cycle:** 5 minutes, configurable via COUNCIL_CYCLE_SECONDS
- **Knowledge triple-store:** Obsidian vault + SQLite + ChromaDB semantic search

### Suit SDK
The Suit SDK compiles expression trees (JSON, turtle DSL, or natural language) into optimized Luau with @native codegen and SIMD/NEON vectorization. Pipeline: Parse -> Optimize -> Codegen -> Encode.

---
*This record grows as Pete explores. New discoveries are appended with timestamps and role attribution.*
