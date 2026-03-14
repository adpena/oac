from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "VISION.md",
    "ROADMAP.md",
    "docs/spec/000-principles.md",
    "docs/spec/001-canonical-format.md",
    "docs/spec/002-adapter-model.md",
    "docs/spec/003-target-mappings.md",
    "docs/spec/004-learning-loop.md",
    "docs/spec/005-security-and-distribution.md",
    "docs/spec/006-outstanding-upgrades.md",
    "docs/spec/007-ingest-architecture.md",
    "docs/spec/008-ingest-support-matrix.md",
    "docs/spec/009-proposal-and-promotion.md",
    "docs/spec/010-eval-and-conformance.md",
    "docs/spec/011-snapshots-and-release.md",
    "prompts/codex-bootstrap.md",
    "prompts/codex-task-template.md",
    "examples/hooks/python/post_hydrate_notice.py",
    "examples/hooks/typescript/post_hydrate_notice.ts",
    "examples/hooks/go/post_hydrate_notice.go",
    "examples/hooks/rust/post_hydrate_notice.rs",
    "examples/hooks/zig/post_hydrate_notice.zig",
    "examples/hooks/wasm/oac_hook.wit",
    "examples/bridges/mcp/hook_bridge_server.py",
    "examples/bridges/webmcp/browser_hook_bridge.ts",
    "tests/fixtures/ingest/README.md",
    "tests/fixtures/proposals/README.md",
    "tests/test_ingest_fixtures.py",
    "scripts/smoke_all.py",
    "tests/test_proposal_fixtures.py",
    "tests/test_eval_and_promotion.py",
]


def test_required_high_signal_artifacts_exist() -> None:
    for rel in REQUIRED:
        assert (ROOT / rel).exists(), f"Missing artifact: {rel}"
