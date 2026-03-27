from pathlib import Path

import yaml

from oac.catalog import get_target, list_targets
from oac.profile_io import scaffold_profile, validate_profile

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "examples" / "adapter-profiles"


def test_all_bundled_profiles_validate() -> None:
    for path in PROFILE_DIR.glob("*.default.yaml"):
        profile = validate_profile(path)
        assert profile.profile_name.endswith(".default")
        assert profile.surfaces


def test_catalog_has_expected_targets() -> None:
    targets = {entry.target.value for entry in list_targets()}
    assert {"codex", "openclaw", "claude-code", "opencode", "gemini", "mcp", "webmcp", "roblox-embodiment"} <= targets


def test_gemini_profile_has_hooks_and_wrappers() -> None:
    profile = get_target("gemini").default_profile
    assert profile.hooks
    assert profile.wrappers


def test_opencode_profile_uses_typescript_hook_example() -> None:
    profile = get_target("opencode").default_profile
    assert profile.hooks
    assert profile.hooks[0].runtime.value == "typescript"


def test_custom_profile_can_remap_surface_paths(tmp_path: Path) -> None:
    path = scaffold_profile("codex", tmp_path / "codex.example.test.yaml")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    surfaces = payload.get("surfaces", [])
    for surface in surfaces:
        if surface.get("name") == "project-rules":
            surface["path"] = "TEAM_AGENTS.md"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    profile = validate_profile(path)
    assert profile.surfaces[0].path == "TEAM_AGENTS.md"
