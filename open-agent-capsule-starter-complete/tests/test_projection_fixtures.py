from pathlib import Path

from oac.adapters import get_adapter
from oac.adapters.base import AdapterOptions

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-capsule"
FIXTURES = ROOT / "tests" / "fixtures" / "projections"
TARGETS = ["codex", "openclaw", "claude-code", "opencode", "gemini", "mcp", "webmcp"]


def _tree(root: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            payload[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
    return payload


def test_hydrate_matches_projection_fixtures(tmp_path: Path) -> None:
    for target in TARGETS:
        destination = tmp_path / target
        adapter = get_adapter(target)
        adapter.hydrate(EXAMPLE, destination, AdapterOptions())
        assert _tree(destination) == _tree(FIXTURES / target), target


def test_hydrate_respects_profile_path_override(tmp_path: Path) -> None:
    profile = tmp_path / "codex.example.test.yaml"
    profile.write_text(
        """
format: oac.adapter-profile.v0
profile_name: codex.example.test
target: codex
description: local override
surfaces:
  - name: project-rules
    path: TEAM_AGENTS.md
    ownership_mode: managed-section
    portability: portable
    notes: local override
  - name: skill-root
    path: .team/skills
    ownership_mode: managed-file
    portability: portable
    notes: local override
  - name: projection-metadata
    path: .team/projection.json
    ownership_mode: managed-file
    portability: portable
    notes: local override
flags: []
mappings: []
hooks: []
wrappers: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    adapter = get_adapter("codex")
    destination = tmp_path / "custom"
    adapter.hydrate(EXAMPLE, destination, AdapterOptions(profile_path=str(profile)))
    assert (destination / "TEAM_AGENTS.md").exists()
    assert (destination / ".team/skills/onboarding/SKILL.md").exists()
    assert (destination / ".team/projection.json").exists()
