import shutil
from pathlib import Path

from oac.adapters import AdapterOptions, get_adapter
from oac.evals import evaluate_capsule
from oac.proposals import (
    ProposalDisposition,
    create_proposal_bundle,
    preview_promotion,
    revert_promotion,
)
from oac.snapshot import create_snapshot

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-capsule"


def test_eval_passes_for_example() -> None:
    report = evaluate_capsule(EXAMPLE)
    assert report.passed is True
    assert "codex" in report.targets
    assert any(check.name == "manifest" for check in report.checks)


def test_promote_and_revert_round_trip(tmp_path: Path) -> None:
    capsule = tmp_path / "capsule"
    shutil.copytree(EXAMPLE, capsule)
    projection = tmp_path / "codex"

    adapter = get_adapter("codex")
    adapter.hydrate(capsule, projection, AdapterOptions())
    ingest_report = adapter.ingest(projection, capsule, AdapterOptions())
    bundle = create_proposal_bundle(capsule, ingest_report)

    promotable_paths = {
        record.canonical_path
        for record in bundle.records
        if record.disposition == ProposalDisposition.PROMOTABLE and record.canonical_path
    }
    assert "procedures/behavior/codex-open-agent-capsule-projection.md" in promotable_paths

    eval_report = evaluate_capsule(capsule, bundle, mode="promotion-eval")
    assert eval_report.passed is True

    promotion_report = preview_promotion(bundle, capsule, apply=True, eval_passed=True)
    promoted_file = capsule / "procedures" / "behavior" / "codex-open-agent-capsule-projection.md"
    assert promoted_file.exists()
    assert promotion_report.change_count >= 1

    promotion_json = (
        capsule / ".oac" / "promotions" / promotion_report.promotion_id / "promotion.json"
    )
    revert_report = revert_promotion(promotion_json, capsule, apply=True)
    assert revert_report.reverted_count >= 1
    assert not promoted_file.exists()


def test_snapshot_is_deterministic(tmp_path: Path) -> None:
    output_a = tmp_path / "snapshots-a"
    output_b = tmp_path / "snapshots-b"
    report_a = create_snapshot(EXAMPLE, output_a)
    report_b = create_snapshot(EXAMPLE, output_b)
    assert report_a.snapshot_id == report_b.snapshot_id
    assert Path(report_a.archive_path).exists()
    assert Path(report_b.metadata_path).exists()
