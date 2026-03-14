//! Small example hook used by starter adapter profiles.
//!
//! This starter keeps the Rust example dependency-free and intentionally boring.
//! In a real setup you would parse the hook payload, validate sidecars, or notify an
//! external system after an opt-in hydrate step.

use std::io::{self, Write};

fn main() {
    let payload = r#"{"event":"post-hydrate","tool":"oac","status":"ok","note":"rust starter hook placeholder"}"#;
    let mut stdout = io::stdout();
    stdout.write_all(payload.as_bytes()).expect("write stdout");
    stdout.write_all(b"
").expect("write newline");
}
