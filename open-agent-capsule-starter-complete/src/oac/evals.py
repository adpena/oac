from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oac.adapters import AdapterOptions, get_adapter
from oac.capsule import load_capsule
from oac.io import validate_manifest
from oac.proposals import ProposalBundle, materialize_bundle


@dataclass(slots=True)
class EvalCheck:
    """One deterministic structural check."""

    name: str
    passed: bool
    summary: str


@dataclass(slots=True)
class EvalReport:
    """Starter eval slice for canonical integrity and adapter round-trips."""

    capsule_id: str
    passed: bool
    mode: str
    targets: list[str] = field(default_factory=list)
    checks: list[EvalCheck] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def evaluate_capsule(
    capsule_root: Path,
    proposal_bundle: ProposalBundle | None = None,
    *,
    target_names: list[str] | None = None,
    mode: str = "eval",
) -> EvalReport:
    """Run a deterministic starter eval slice.

    The eval is intentionally structural: validate the manifest, reload the capsule, and prove
    every enabled target can hydrate and ingest from the staged capsule. That gives the starter a
    real gate without pretending to solve semantic evaluation yet.
    """

    notes = [
        "This starter eval is structural, not model-quality scoring.",
        "Hydrate and ingest are exercised for every selected target.",
    ]
    stage_root = capsule_root
    temporary_dir: tempfile.TemporaryDirectory[str] | None = None

    if proposal_bundle is not None:
        temporary_dir = tempfile.TemporaryDirectory(prefix="oac-eval-")
        stage_root = Path(temporary_dir.name) / "capsule"
        shutil.copytree(capsule_root, stage_root)
        materialize_bundle(proposal_bundle, stage_root)
        notes.append("Promotable proposal records were staged into a temporary capsule copy.")

    passed = True
    checks: list[EvalCheck] = []

    try:
        validation = validate_manifest(stage_root)
        checks.append(EvalCheck("manifest", True, f"valid manifest: {validation.capsule_id}"))
        capsule = load_capsule(stage_root)
        checks.append(EvalCheck("capsule-load", True, "canonical files load successfully"))
    except Exception as exc:  # pragma: no cover - kept explicit for CLI behavior
        if temporary_dir is not None:
            temporary_dir.cleanup()
        return EvalReport(
            capsule_id=proposal_bundle.capsule_id if proposal_bundle else "<unknown>",
            passed=False,
            mode=mode,
            checks=[EvalCheck("manifest", False, str(exc))],
            notes=notes,
        )

    selected_targets = target_names or [
        target.name.value for target in capsule.manifest.targets if target.enabled
    ]
    for target_name in selected_targets:
        adapter = get_adapter(target_name)
        with tempfile.TemporaryDirectory(prefix=f"oac-{target_name}-") as temp_dir:
            projection_root = Path(temp_dir) / target_name
            try:
                projection = adapter.hydrate(stage_root, projection_root, AdapterOptions())
                ingest = adapter.ingest(projection_root, stage_root, AdapterOptions())
                summary = (
                    f"hydrate={len(projection.artifacts)} artifacts, "
                    f"ingest={ingest.stats.candidate_count} candidates"
                )
                checks.append(EvalCheck(f"target:{target_name}", True, summary))
            except Exception as exc:  # pragma: no cover - kept explicit for CLI behavior
                checks.append(EvalCheck(f"target:{target_name}", False, str(exc)))
                passed = False

    if temporary_dir is not None:
        temporary_dir.cleanup()

    return EvalReport(
        capsule_id=capsule.manifest.capsule_id,
        passed=passed and all(check.passed for check in checks),
        mode=mode,
        targets=selected_targets,
        checks=checks,
        notes=notes,
    )


def eval_report_to_dict(report: EvalReport) -> dict[str, Any]:
    return {
        "capsule_id": report.capsule_id,
        "passed": report.passed,
        "mode": report.mode,
        "targets": report.targets,
        "notes": report.notes,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "summary": check.summary,
            }
            for check in report.checks
        ],
    }


def render_eval_report(report: EvalReport) -> str:
    lines = [
        f"{report.mode}: {report.capsule_id}",
        f"passed: {'yes' if report.passed else 'no'}",
        f"targets: {', '.join(report.targets)}",
    ]
    for check in report.checks:
        lines.append(f"- {'pass' if check.passed else 'fail'}: {check.name} -> {check.summary}")
    for note in report.notes:
        lines.append(f"note: {note}")
    return "\n".join(lines)
