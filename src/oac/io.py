from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from oac.models import CapsuleManifest, ValidationResult, check_compatibility


def resolve_manifest_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / "manifest.yaml"
    if not candidate.exists():
        raise FileNotFoundError(f"Manifest not found: {candidate}")
    return candidate


def load_manifest(path: str | Path) -> CapsuleManifest:
    manifest_path = resolve_manifest_path(path)
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise TypeError("Manifest root must be a mapping/object.")

    format_id = payload.get("format", "oac.v0")
    check_compatibility("manifest", format_id)

    return CapsuleManifest.model_validate(payload)


def validate_manifest(path: str | Path) -> ValidationResult:
    manifest_path = resolve_manifest_path(path)
    manifest = load_manifest(manifest_path)
    return ValidationResult(
        manifest_path=str(manifest_path),
        capsule_id=manifest.capsule_id,
        target_count=len(manifest.targets),
        format=manifest.format,
    )


def write_text(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def write_if_changed(path: str | Path, text: str) -> bool:
    """Write text only if it differs from current content. Returns True if written."""
    target = Path(path)
    if target.exists():
        if target.read_text(encoding="utf-8") == text:
            return False
    write_text(target, text)
    return True


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False)
