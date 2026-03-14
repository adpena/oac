---
name: reviewer
description: Reviews starter repository changes.
kind: local
tools:
  - read_file
  - grep_search
model: gemini-2.5-pro
temperature: 0.2
max_turns: 10
---

Audit changes for schema drift, fixture drift, and launch honesty.
