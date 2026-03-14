from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from oac.catalog import render_profile_yaml
from oac.models import check_compatibility
from oac.profile_models import AdapterProfile


def load_profile(path: str | Path) -> AdapterProfile:
    """Load and validate an adapter profile from YAML."""

    profile_path = Path(path)
    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise TypeError("Adapter profile root must be a mapping/object.")

    format_id = payload.get("format", "oac.adapter-profile.v0")
    check_compatibility("profile", format_id)

    return AdapterProfile.model_validate(payload)


def validate_profile(path: str | Path) -> AdapterProfile:
    """Load and validate an adapter profile, returning the typed model."""

    return load_profile(path)


def scaffold_profile(target: str, path: str | Path) -> Path:
    """Write a bundled adapter profile template to disk."""

    profile_path = Path(path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(render_profile_yaml(target), encoding="utf-8")
    return profile_path


def dump_yaml(data: dict[str, Any]) -> str:
    """Serialize a dictionary as YAML using starter defaults."""

    return yaml.safe_dump(data, sort_keys=False)
