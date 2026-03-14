# Hook examples

These are small starter examples for adapter-profile hooks.

Rules:

- hooks are disabled by default in bundled profiles
- hooks must stay explicit and reviewable
- hooks may enrich or notify, but should not silently mutate canonical state

Included runtimes:

- Python
- TypeScript
- Go
- Rust
- Zig
- WASM component sketch

All examples use the same payload file shape in `hook-payload.example.json`.
See `docs/spec/002-adapter-model.md` for the hook and wrapper boundary.
