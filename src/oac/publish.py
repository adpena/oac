from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from oac.snapshot import SnapshotReport


@dataclass(slots=True)
class PublishReport:
    """Metadata for a published capsule release."""

    capsule_id: str
    snapshot_id: str
    publish_root: str
    archive_name: str
    metadata_name: str
    notes: list[str] = field(default_factory=list)


def publish_snapshot(report: SnapshotReport, publish_root: Path) -> PublishReport:
    """Package a snapshot into a standardized registry layout."""

    # Standard layout: <publish_root>/<capsule_id>/<snapshot_id>/
    target_dir = publish_root / report.capsule_id / report.snapshot_id
    target_dir.mkdir(parents=True, exist_ok=True)

    archive_source = Path(report.archive_path)
    metadata_source = Path(report.metadata_path)
    checksums_source = Path(report.checksums_path)

    shutil.copy2(archive_source, target_dir / archive_source.name)
    shutil.copy2(metadata_source, target_dir / "snapshot.json")
    shutil.copy2(checksums_source, target_dir / "checksums.json")

    if report.signature_path:
        shutil.copy2(Path(report.signature_path), target_dir / "signature.sig")

    return PublishReport(
        capsule_id=report.capsule_id,
        snapshot_id=report.snapshot_id,
        publish_root=str(publish_root),
        archive_name=archive_source.name,
        metadata_name="snapshot.json",
        notes=[f"Snapshot published to local registry layout at {target_dir}"],
    )
