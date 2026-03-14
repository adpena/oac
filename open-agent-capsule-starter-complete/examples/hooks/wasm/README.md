# WASM hook sketch

This directory shows how a hook could be packaged as a WebAssembly component without making
WASM the canonical representation of the capsule.

Files:

- `oac_hook.wit` — typed component interface for the hook contract
- `guest.rs` — illustrative guest implementation sketch
- `host.ts` — illustrative host runner sketch that adapts the normal OAC hook payload into the component interface

This starter does not compile the component. It provides a portable shape for future work.
