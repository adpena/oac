from __future__ import annotations

import hashlib
import hmac
import json
import shutil
import subprocess
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
    signature_path: str | None = None
    signature_kind: str | None = None
    notes: list[str] = field(default_factory=list)


def create_snapshot(
    capsule_root: Path, output_root: Path, *, sign_key: Path | None = None
) -> SnapshotReport:
    """Package the capsule into a local tar.gz plus checksum manifest.

    The snapshot is deterministic with respect to file paths and contents.
    If a sign_key is provided, a symmetric HMAC-SHA256 signature of the content digest is created.
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

    signature_path: Path | None = None
    signature_kind: str | None = None

    if sign_key and sign_key.is_file():
        key_bytes = sign_key.read_bytes()
        digest_hex = digest.hexdigest()

        if b"BEGIN OPENSSH PRIVATE KEY" in key_bytes:
            # Asymmetric SSH signing (Ed25519)
            signature_kind = "asymmetric-ssh"
            signature_path = snapshot_dir / "signature.sig"
            # We use a temporary file for the digest to sign it via ssh-keygen
            digest_file = snapshot_dir / "digest.txt"
            digest_file.write_text(digest_hex, encoding="utf-8")
            try:
                cmd = [
                    "ssh-keygen",
                    "-Y",
                    "sign",
                    "-n",
                    "oac",
                    "-f",
                    str(sign_key),
                    str(digest_file),
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                # ssh-keygen -Y sign creates <file>.sig
                sig_file = snapshot_dir / "digest.txt.sig"
                if sig_file.exists():
                    shutil.move(sig_file, signature_path)
                    digest_file.unlink()
            except Exception as exc:
                signature_path = None
                signature_kind = None
                print(f"Warning: Asymmetric signing failed: {exc}")
        else:
            # Fallback to symmetric HMAC
            signature_kind = "symmetric-hmac"
            mac = hmac.new(key_bytes, digest_hex.encode("utf-8"), hashlib.sha256).hexdigest()
            signature_path = snapshot_dir / "signature.sig"
            signature_path.write_text(mac + "\n", encoding="utf-8")

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
                "signed": signature_path is not None,
                "signature": signature_path.name if signature_path else None,
                "signature_kind": signature_kind,
                "notes": [
                    "Starter snapshots are checksummed.",
                    "Symmetric (HMAC) or Asymmetric (SSH) signatures are created "
                    "if a sign_key is provided.",
                    "Promotion and prior snapshot directories are excluded from the archive.",
                ],
            },
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )

    notes = [
        "The snapshot identifier is a content digest, not a timestamp.",
    ]
    if signature_path:
        notes.append(f"Snapshot was signed using {signature_kind}.")
    else:
        notes.append("Signing remains a future distribution step if no key is provided.")

    return SnapshotReport(
        snapshot_id=snapshot_id,
        capsule_id=manifest.capsule_id,
        archive_path=str(archive_path),
        metadata_path=str(metadata_path),
        checksums_path=str(checksums_path),
        file_count=len(files),
        signature_path=str(signature_path) if signature_path else None,
        signature_kind=signature_kind,
        notes=notes,
    )


def snapshot_report_to_dict(report: SnapshotReport) -> dict[str, Any]:
    return {
        "snapshot_id": report.snapshot_id,
        "capsule_id": report.capsule_id,
        "archive_path": report.archive_path,
        "metadata_path": report.metadata_path,
        "checksums_path": report.checksums_path,
        "file_count": report.file_count,
        "signature_path": report.signature_path,
        "signature_kind": report.signature_kind,
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
