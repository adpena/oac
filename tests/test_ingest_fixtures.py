import json
from pathlib import Path

from oac.adapters import AdapterOptions, get_adapter
from oac.ingest import ingest_report_to_dict

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-capsule"
PROJECTION_FIXTURES = ROOT / "tests" / "fixtures" / "projections"
INGEST_FIXTURES = ROOT / "tests" / "fixtures" / "ingest"
TARGETS = ["codex", "openclaw", "claude-code", "opencode", "gemini", "mcp", "webmcp", "roblox-embodiment"]


def test_ingest_matches_fixtures() -> None:
    for target in TARGETS:
        adapter = get_adapter(target)
        report = adapter.ingest(PROJECTION_FIXTURES / target, EXAMPLE, AdapterOptions())
        expected = json.loads((INGEST_FIXTURES / f"{target}.json").read_text(encoding="utf-8"))
        assert ingest_report_to_dict(report) == expected, target


def test_ingest_respects_profile_path_override(tmp_path: Path) -> None:
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
  - name: identity
    path: .team/identity
    ownership_mode: managed-file
    portability: portable
    notes: local override
  - name: memory-root
    path: .team/memory
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
    report = adapter.ingest(destination, EXAMPLE, AdapterOptions(profile_path=str(profile)))
    payload = ingest_report_to_dict(report)
    assert payload["stats"]["candidate_count"] == 7
    assert payload["candidates"][0]["source_path"] == "TEAM_AGENTS.md"
    assert payload["candidates"][1]["source_path"] == ".team/skills/onboarding/SKILL.md"
    assert payload["candidates"][2]["source_path"] == ".team/identity/identity.md"
    assert payload["candidates"][3]["source_path"] == ".team/identity/persona.md"
    assert payload["candidates"][4]["source_path"] == ".team/identity/user-model.md"
