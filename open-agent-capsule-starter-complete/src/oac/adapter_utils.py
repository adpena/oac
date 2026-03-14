from __future__ import annotations

import json
import re
from pathlib import Path
from string import Formatter
from typing import Any

from oac.catalog import get_target
from oac.io import write_text
from oac.profile_io import load_profile
from oac.profile_models import AdapterProfile

_TEMPLATE_FIELD_RE = re.compile(r"\{[^{}]+\}")


def load_effective_profile(target: str, profile_path: str | None = None) -> AdapterProfile:
    if profile_path:
        profile = load_profile(profile_path)
        if profile.target.value != target:
            raise ValueError(
                f"Profile target mismatch: expected {target}, got {profile.target.value}"
            )
        return profile
    return get_target(target).default_profile


def surface_template(profile: AdapterProfile, name: str, fallback: str) -> str:
    for surface in profile.surfaces:
        if surface.name == name:
            return surface.path
    return fallback


def surface_path(profile: AdapterProfile, name: str, fallback: str, **vars: Any) -> str:
    template = surface_template(profile, name, fallback)
    fields = Formatter().parse(template)
    values = {field_name: vars.get(field_name, "") for _, field_name, _, _ in fields if field_name}
    values.update(vars)
    return template.format(**values)


def template_to_glob(template: str) -> str:
    return _TEMPLATE_FIELD_RE.sub("*", template)


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=False) + "\n")


def record_artifact(report, path: str, summary: str, ownership_mode):
    from oac.adapters.base import ProjectionArtifact

    report.artifacts.append(
        ProjectionArtifact(path=path, summary=summary, ownership_mode=ownership_mode)
    )
