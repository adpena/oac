---
name: adapter-profile-author
description: Use when changing bundled adapter profiles, surface paths, hooks, wrappers, or profile validation behavior.
---

# Adapter profile author

1. Read `docs/spec/002-adapter-model.md` and `docs/spec/003-target-mappings.md`.
2. Keep the profile focused on projection shape, not canonical meaning.
3. Update the bundled profile under `examples/adapter-profiles/`.
4. Regenerate schemas if the model changed.
5. Regenerate fixtures if emitted paths changed.
6. Keep hooks opt-in by default.
7. Run `make check`.
