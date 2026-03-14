from __future__ import annotations

import hashlib
import json
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oac.io import load_manifest

_SKIPPED_PREFIXES = (
    ".oac/promotions/",
    ".oac/snapshots/",
    ".pytest_cache/",
    ".ruff_cache/",
    "__pycache__/",
)


@dataclass(slots=True)
class SnapshotReport:
    """Metadata for a local deterministic capsule snapshot."""

    snapshot_id: str
    capsule_id: str
    archive_path: str
    metadata_path: str
    checksums_path: str
    file_count: int
    notes: list[str] = field(default_factory=list)


def create_snapshot(capsule_root: Path, output_root: Path) -> SnapshotReport:
    """Package the capsule into a local tar.gz plus checksum manifest.

    The snapshot is deterministic with respect to file paths and contents. Signing stays a later
    step, but checksums and a stable snapshot identifier give the starter a real distribution seam.
    """

    manifest = load_manifest(capsule_root)
    files = list(_iter_snapshot_files(capsule_root))
    digest = hashlib.sha256()
    checksums: dict[str, str] = {}
    for path in files:
        relative = path.relative_to(capsule_root).as_posix()
        content = path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        checksums[relative] = file_hash
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")

    snapshot_id = f"{manifest.capsule_id}-{digest.hexdigest()[:12]}"
    snapshot_dir = output_root / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    archive_path = output_root / f"{snapshot_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in files:
            relative = path.relative_to(capsule_root)
            archive.add(path, arcname=f"{manifest.capsule_id}/{relative.as_posix()}")

    checksums_path = snapshot_dir / "checksums.json"
    metadata_path = snapshot_dir / "snapshot.json"
    checksums_path.write_text(
        json.dumps(checksums, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata_path.write_text(
        json.dumps(
            {
                "snapshot_id": snapshot_id,
                "capsule_id": manifest.capsule_id,
                "archive": archive_path.name,
                "file_count": len(files),
                "signed": False,
                "notes": [
                    "Starter snapshots are checksummed but not signed yet.",
                    "Promotion and prior snapshot directories are excluded from the archive.",
                ],
            },
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return SnapshotReport(
        snapshot_id=snapshot_id,
        capsule_id=manifest.capsule_id,
        archive_path=str(archive_path),
        metadata_path=str(metadata_path),
        checksums_path=str(checksums_path),
        file_count=len(files),
        notes=[
            "The snapshot identifier is a content digest, not a timestamp.",
            "Signing remains a future distribution step.",
        ],
    )


def snapshot_report_to_dict(report: SnapshotReport) -> dict[str, Any]:
    return {
        "snapshot_id": report.snapshot_id,
        "capsule_id": report.capsule_id,
        "archive_path": report.archive_path,
        "metadata_path": report.metadata_path,
        "checksums_path": report.checksums_path,
        "file_count": report.file_count,
        "notes": report.notes,
    }


def _iter_snapshot_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(_SKIPPED_PREFIXES):
            continue
        if any(relative.startswith(prefix) for prefix in _SKIPPED_PREFIXES):
            continue
        yield path
