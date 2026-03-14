import json
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


def test_revert_blocked_if_modified(tmp_path: Path) -> None:
    import pytest

    capsule = tmp_path / "capsule"
    shutil.copytree(EXAMPLE, capsule)
    projection = tmp_path / "codex"

    adapter = get_adapter("codex")
    adapter.hydrate(capsule, projection, AdapterOptions())
    ingest_report = adapter.ingest(projection, capsule, AdapterOptions())
    bundle = create_proposal_bundle(capsule, ingest_report)

    promotion_report = preview_promotion(bundle, capsule, apply=True, eval_passed=True)
    promoted_file = capsule / "procedures" / "behavior" / "codex-open-agent-capsule-projection.md"

    # Modify the file after promotion
    promoted_file.write_text("Modified after promotion\n")

    promotion_json = (
        capsule / ".oac" / "promotions" / promotion_report.promotion_id / "promotion.json"
    )

    # Should raise ValueError
    with pytest.raises(ValueError, match="Cannot revert: .* was modified. Use --force."):
        revert_promotion(promotion_json, capsule, apply=True)

    # Should succeed with force=True
    revert_report = revert_promotion(promotion_json, capsule, apply=True, force=True)
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
    assert report_a.signature_path is None


def test_snapshot_signing(tmp_path: Path) -> None:
    output = tmp_path / "snapshots-signed"
    key_file = tmp_path / "secret.key"
    key_file.write_bytes(b"test-secret-key-1234")

    report = create_snapshot(EXAMPLE, output, sign_key=key_file)

    assert report.signature_path is not None
    sig_path = Path(report.signature_path)
    assert sig_path.exists()

    # Verify the metadata indicates it was signed
    metadata = json.loads(Path(report.metadata_path).read_text(encoding="utf-8"))
    assert metadata["signed"] is True
    assert metadata["signature"] == sig_path.name


def test_proposal_conflict_detection(tmp_path: Path) -> None:
    from oac.adapters.base import (
        IngestCandidate,
        IngestReport,
        LossinessKind,
        OwnershipMode,
        PortabilityClass,
    )
    from oac.proposals import ProposalDisposition

    capsule = tmp_path / "capsule"
    shutil.copytree(EXAMPLE, capsule)

    # Create two candidates that will map to the same slug (and therefore the same canonical path)
    cand1 = IngestCandidate(
        candidate_id="cand1",
        kind="procedure.workflow",
        suggested_canonical_kind="procedure.workflow",
        source_path="surface/workflow_a.md",
        summary="Same Name Workflow",
        portability=PortabilityClass.PORTABLE,
        ownership_mode=OwnershipMode.MANAGED_FILE,
        lossiness=LossinessKind.PARTIALLY_LOSSLESS,
        surface_name="surface",
        content="First version",
        candidate_path_hint="hint1",
        metadata={"parser": "markdown"},
    )

    cand2 = IngestCandidate(
        candidate_id="cand2",
        kind="procedure.workflow",
        suggested_canonical_kind="procedure.workflow",
        source_path="surface/workflow_b.md",
        summary="Same Name Workflow",
        portability=PortabilityClass.PORTABLE,
        ownership_mode=OwnershipMode.MANAGED_FILE,
        lossiness=LossinessKind.PARTIALLY_LOSSLESS,
        surface_name="surface",
        content="Second version",
        candidate_path_hint="hint2",
        metadata={"parser": "markdown"},
    )

    report = IngestReport(
        target="codex", source_root=".", support="partial", candidates=[cand1, cand2]
    )

    bundle = create_proposal_bundle(capsule, report)

    assert bundle.stats.total == 2
    assert bundle.stats.conflict == 2
    assert bundle.stats.promotable == 0
    assert bundle.records[0].disposition == ProposalDisposition.CONFLICT
    assert bundle.records[1].disposition == ProposalDisposition.CONFLICT
    assert "Conflict" in bundle.records[0].rationale
