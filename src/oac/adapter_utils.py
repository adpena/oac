from __future__ import annotations

import json
import re
from pathlib import Path
from string import Formatter
from typing import Any

from oac.catalog import get_target
from oac.io import write_if_changed, write_text
from oac.profile_io import load_profile
from oac.profile_models import AdapterProfile

_TEMPLATE_FIELD_RE = re.compile(r"\{[^{}]+\}")


def load_effective_profile(target: str, profile_path: str | None = None) -> AdapterProfile:
    default_profile = get_target(target).default_profile
    if not profile_path:
        return default_profile

    custom_profile = load_profile(profile_path)
    if custom_profile.target.value != target:
        raise ValueError(
            f"Profile target mismatch: expected {target}, got {custom_profile.target.value}"
        )

    return merge_profiles(default_profile, custom_profile)


def merge_profiles(base: AdapterProfile, overlay: AdapterProfile) -> AdapterProfile:
    """Perform a keyed merge of two adapter profiles."""
    result = base.model_copy(deep=True)

    if overlay.description:
        result.description = overlay.description

    # Keyed merges for list fields
    def merge_list(base_list, overlay_list, key_attr):
        base_map = {getattr(item, key_attr): item for item in base_list}
        for item in overlay_list:
            base_map[getattr(item, key_attr)] = item
        return list(base_map.values())

    result.surfaces = merge_list(result.surfaces, overlay.surfaces, "name")
    result.flags = merge_list(result.flags, overlay.flags, "name")
    result.hooks = merge_list(result.hooks, overlay.hooks, "name")
    result.wrappers = merge_list(result.wrappers, overlay.wrappers, "name")

    # Mappings are keyed by canonical_kind
    mappings_map = {m.canonical_kind: m for m in result.mappings}
    for m in overlay.mappings:
        mappings_map[m.canonical_kind] = m
    result.mappings = list(mappings_map.values())

    return result


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


def write_json_if_changed(path: str | Path, payload: dict[str, Any]) -> bool:
    return write_if_changed(path, json.dumps(payload, indent=2, sort_keys=False) + "\n")


def record_artifact(report, path: str, summary: str, ownership_mode, updated: bool = True):
    from oac.adapters.base import ProjectionArtifact

    if updated:
        report.updated_count += 1
    else:
        report.unchanged_count += 1

    report.artifacts.append(
        ProjectionArtifact(path=path, summary=summary, ownership_mode=ownership_mode)
    )
