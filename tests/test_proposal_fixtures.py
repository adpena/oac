import json
from pathlib import Path

from oac.adapters import AdapterOptions, get_adapter
from oac.proposals import create_proposal_bundle, proposal_bundle_to_dict

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-capsule"
PROJECTION_FIXTURES = ROOT / "tests" / "fixtures" / "projections"
PROPOSAL_FIXTURES = ROOT / "tests" / "fixtures" / "proposals"
TARGETS = ["codex", "openclaw", "claude-code", "opencode", "gemini", "mcp", "webmcp", "roblox-embodiment"]


def test_proposals_match_fixtures() -> None:
    for target in TARGETS:
        adapter = get_adapter(target)
        ingest_report = adapter.ingest(PROJECTION_FIXTURES / target, EXAMPLE, AdapterOptions())
        bundle = create_proposal_bundle(EXAMPLE, ingest_report)
        expected = json.loads((PROPOSAL_FIXTURES / f"{target}.json").read_text(encoding="utf-8"))
        assert proposal_bundle_to_dict(bundle) == expected, target


def test_proposal_respects_profile_path_override(tmp_path: Path) -> None:
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
    ingest_report = adapter.ingest(destination, EXAMPLE, AdapterOptions(profile_path=str(profile)))
    bundle = create_proposal_bundle(EXAMPLE, ingest_report)
    payload = proposal_bundle_to_dict(bundle)
    assert payload["records"][0]["source_path"] == "TEAM_AGENTS.md"
    assert payload["records"][1]["canonical_path"] == "skills/onboarding/SKILL.md"
