from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oac.io import validate_manifest  # noqa: E402
from oac.profile_io import validate_profile  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from smoke_all import run_smoke  # noqa: E402

PROFILE_FILES = [
    ROOT / "examples" / "adapter-profiles" / "codex.default.yaml",
    ROOT / "examples" / "adapter-profiles" / "openclaw.default.yaml",
    ROOT / "examples" / "adapter-profiles" / "claude-code.default.yaml",
    ROOT / "examples" / "adapter-profiles" / "opencode.default.yaml",
    ROOT / "examples" / "adapter-profiles" / "gemini.default.yaml",
    ROOT / "examples" / "adapter-profiles" / "mcp.default.yaml",
    ROOT / "examples" / "adapter-profiles" / "webmcp.default.yaml",
]


def main() -> int:
    subprocess.run(["ruff", "check", "."], check=True, cwd=ROOT)
    subprocess.run(["ruff", "format", "--check", "."], check=True, cwd=ROOT)

    result = pytest.main(["-q"], plugins=[])
    if result != 0:
        return int(result)

    manifest = validate_manifest(ROOT / "examples" / "hello-capsule")
    print(f"valid manifest: {manifest.capsule_id}")

    for path in PROFILE_FILES:
        profile = validate_profile(path)
        print(f"valid profile: {profile.profile_name}")

    run_smoke("all", quiet=True)
    print("smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
