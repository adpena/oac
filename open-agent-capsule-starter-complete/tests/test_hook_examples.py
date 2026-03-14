from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "examples/hooks/python/post_hydrate_notice.py",
    "examples/hooks/typescript/post_hydrate_notice.ts",
    "examples/hooks/go/post_hydrate_notice.go",
    "examples/hooks/rust/post_hydrate_notice.rs",
    "examples/hooks/zig/post_hydrate_notice.zig",
    "examples/hooks/wasm/README.md",
    "examples/hooks/wasm/oac_hook.wit",
    "examples/hooks/wasm/guest.rs",
    "examples/hooks/wasm/host.ts",
    "examples/hooks/hook-payload.example.json",
    "examples/bridges/mcp/hook_bridge_server.py",
    "examples/bridges/webmcp/browser_hook_bridge.ts",
]


def test_polyglot_hook_and_bridge_examples_exist() -> None:
    for rel in REQUIRED:
        assert (ROOT / rel).exists(), f"Missing example artifact: {rel}"
