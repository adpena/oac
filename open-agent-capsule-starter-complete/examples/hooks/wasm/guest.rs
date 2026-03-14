//! Illustrative WebAssembly component guest for the OAC hook contract.
//!
//! This file is intentionally pseudocode-adjacent: it shows the shape of a component guest
//! without committing the starter pack to a particular code generator or runtime today.

// bindings::export!(Component with_types_in bindings);

struct Component;

impl Component {
    fn run(phase: &str, target: &str) -> (&'static str, String) {
        ("ok", format!("wasm starter hook placeholder for {phase} on {target}"))
    }
}
