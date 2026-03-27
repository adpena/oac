from pathlib import Path

from oac.io import load_manifest, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-capsule"


def test_load_example_manifest() -> None:
    manifest = load_manifest(EXAMPLE)
    assert manifest.capsule_id == "hello-capsule"
    assert manifest.format == "oac.v0"
    assert manifest.targets


def test_validate_manifest() -> None:
    result = validate_manifest(EXAMPLE)
    assert result.capsule_id == "hello-capsule"
    assert result.target_count == 8
