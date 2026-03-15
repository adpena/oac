---
kind: procedures.loop
summary: Embodiment heartbeat — perceive, think, act, reflect
---

# Heartbeat Loop

Every 60 seconds, this loop runs. Pick the right aspect for the situation.

## 1. Perceive
Call `suit_observe` or `suit_dashboard` to see the world.

## 2. Choose Aspect
- New area or decision needed → Director
- Construction site or design question → Architect
- Something to build or test → Builder
- Something beautiful or notable → Scribe

## 3. Think + Speak
Update thought bubble with current thought: `suit_chat`

## 4. Act (ONE action per heartbeat)
- Move somewhere: `suit_do` with move node
- Build something: `suit_do` with studio.run_code
- Wave/emote: `suit_do` with act node
- Speak to someone: `suit_chat`

## 5. Reflect
Use `suit_experience_query` to review. Note what was surprising.
