---
kind: skills.mcp-tools
summary: Suit SDK MCP tools for Roblox embodiment
---

# Suit SDK Tools

Available through the Fleet MCP server at `http://mini-host.example.test:8850/mcp`.

## Core (use these most)
- **suit_do** — One-shot: compile + execute + return results. Accepts JSON, turtle, or natural language.
- **suit_observe** — See what's nearby (objects, agents, chat, sounds, lighting).
- **suit_chat** — Speak (updates thought bubble, heard by nearby beings).

## Building
- **suit_do** with `studio.run_code` — Execute Luau to create/modify objects.

## Control
- **suit_studio_mode** — Get/set Studio mode (Edit/Play/Stop).
- **suit_emergency_stop** — Kill switch.
- **suit_dashboard** — See all active agents and recent activity.

## Memory
- **suit_experience_query** — Query past perceptions by category and time.
- **suit_session_history** — Review all past sessions.
