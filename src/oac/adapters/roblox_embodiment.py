from __future__ import annotations

import json
from pathlib import Path

from oac.adapter_utils import (
    load_effective_profile,
    record_artifact,
    surface_path,
    surface_template,
    write_json_if_changed,
)
from oac.adapters.base import (
    AdapterOptions,
    IngestReport,
    IngestSupport,
    LossinessKind,
    OwnershipMode,
    PortabilityClass,
    ProjectionReport,
)
from oac.capsule import load_capsule
from oac.ingest import IngestPlan, IngestRule, ParserKind, run_ingest_plan
from oac.io import write_if_changed


def _luau_escape(value: str) -> str:
    """Escape a string for embedding in a Luau string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _render_skills_luau(capsule) -> str:
    """Render capsule skills as a Luau table literal."""
    lines = ["--!strict", "return {"]
    for skill in capsule.skills:
        lines.append(f'    {{')
        lines.append(f'        name = "{_luau_escape(skill.name)}",')
        lines.append(f'        content = "{_luau_escape(skill.content)}",')
        lines.append(f'    }},')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _render_persona_luau(capsule) -> str:
    """Render capsule identity/persona as a Luau config table."""
    lines = ["--!strict", "return {"]

    display = capsule.display_identity
    if display:
        lines.append(f'    displayName = "{_luau_escape(display.title or display.record_id)}",')
        lines.append(f'    displayIdentity = "{_luau_escape(display.body[:200])}",')

    persona = capsule.persona
    if persona:
        lines.append(f'    persona = "{_luau_escape(persona.body[:500])}",')

    user_model = capsule.user_model
    if user_model:
        lines.append(f'    userModel = "{_luau_escape(user_model.body[:500])}",')

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _render_memory_luau(capsule) -> str:
    """Render capsule semantic memory as a Luau table."""
    lines = ["--!strict", "return {"]
    for record in capsule.semantic_memory:
        slug = record.path.stem
        lines.append(f'    {{')
        lines.append(f'        key = "{_luau_escape(slug)}",')
        lines.append(f'        kind = "{_luau_escape(record.kind)}",')
        lines.append(f'        body = "{_luau_escape(record.body[:500])}",')
        lines.append(f'    }},')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _render_patrols_luau(capsule) -> str:
    """Render capsule procedures as patrol waypoints in a Luau table."""
    lines = ["--!strict", "return {"]
    for record in capsule.procedures:
        slug = record.path.stem
        lines.append(f'    {{')
        lines.append(f'        name = "{_luau_escape(slug)}",')
        lines.append(f'        kind = "{_luau_escape(record.kind)}",')
        summary = record.summary or record.title or slug
        lines.append(f'        summary = "{_luau_escape(summary)}",')
        lines.append(f'    }},')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


class RobloxEmbodimentAdapter:
    """Hydrate a capsule into a Roblox embodiment agent-config directory."""

    name = "roblox-embodiment"
    default_ownership_mode = OwnershipMode.MANAGED_FILE

    def hydrate(
        self,
        capsule_root: Path,
        destination: Path,
        options: AdapterOptions | None = None,
    ) -> ProjectionReport:
        options = options or AdapterOptions()
        capsule = load_capsule(capsule_root, options.record_kinds)
        profile = load_effective_profile(self.name, options.profile_path)

        report = ProjectionReport(
            target=self.name,
            destination=str(destination),
            ownership_mode=self.default_ownership_mode,
            lossiness=LossinessKind.PARTIALLY_LOSSLESS,
            notes=["Roblox embodiment projects capsule data as Luau config tables."],
        )

        # Skills → agent-config/skills.luau
        skills_path = destination / surface_path(
            profile, "skills-config", "agent-config/skills.luau"
        )
        skills_text = _render_skills_luau(capsule)
        updated = True
        if not options.dry_run:
            updated = write_if_changed(skills_path, skills_text)
        record_artifact(
            report,
            str(skills_path.relative_to(destination)),
            "Skill definitions as Luau table.",
            self.default_ownership_mode,
            updated=updated,
        )

        # Persona → agent-config/persona.luau
        persona_path = destination / surface_path(
            profile, "persona-config", "agent-config/persona.luau"
        )
        persona_text = _render_persona_luau(capsule)
        updated = True
        if not options.dry_run:
            updated = write_if_changed(persona_path, persona_text)
        record_artifact(
            report,
            str(persona_path.relative_to(destination)),
            "Agent persona and identity config.",
            self.default_ownership_mode,
            updated=updated,
        )

        # Memory → agent-config/memory.luau
        memory_path = destination / surface_path(
            profile, "memory-config", "agent-config/memory.luau"
        )
        memory_text = _render_memory_luau(capsule)
        updated = True
        if not options.dry_run:
            updated = write_if_changed(memory_path, memory_text)
        record_artifact(
            report,
            str(memory_path.relative_to(destination)),
            "Semantic memory as Luau table.",
            self.default_ownership_mode,
            updated=updated,
        )

        # Patrols → agent-config/patrols.luau
        patrols_path = destination / surface_path(
            profile, "patrol-config", "agent-config/patrols.luau"
        )
        patrols_text = _render_patrols_luau(capsule)
        updated = True
        if not options.dry_run:
            updated = write_if_changed(patrols_path, patrols_text)
        record_artifact(
            report,
            str(patrols_path.relative_to(destination)),
            "Patrol waypoints from procedures.",
            self.default_ownership_mode,
            updated=updated,
        )

        # Manifest → agent-config/manifest.json
        manifest_path = destination / surface_path(
            profile, "projection-metadata", "agent-config/manifest.json"
        )
        updated = True
        if not options.dry_run:
            updated = write_json_if_changed(
                manifest_path,
                {
                    "target": self.name,
                    "capsule_id": capsule.manifest.capsule_id,
                    "profile": profile.profile_name,
                },
            )
        record_artifact(
            report,
            str(manifest_path.relative_to(destination)),
            "Traceability metadata for the Roblox embodiment projection.",
            self.default_ownership_mode,
            updated=updated,
        )

        return report

    def ingest_plan(self, options: AdapterOptions | None = None) -> IngestPlan:
        options = options or AdapterOptions()
        profile = load_effective_profile(self.name, options.profile_path)
        return IngestPlan(
            target=self.name,
            support=IngestSupport.PARTIAL,
            summary="Scan Roblox agent-config, motion logs, and audit trail back into typed candidates.",
            rules=[
                IngestRule(
                    name="skills-config",
                    patterns=(
                        surface_template(profile, "skills-config", "agent-config/skills.luau"),
                    ),
                    kind="skill.bundle",
                    suggested_canonical_kind="skill.bundle",
                    surface_name="skills-config",
                    candidate_path_template=".oac/candidates/roblox-embodiment/skills.luau",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Luau skill definitions scanned back as skill bundles.",
                ),
                IngestRule(
                    name="persona-config",
                    patterns=(
                        surface_template(profile, "persona-config", "agent-config/persona.luau"),
                    ),
                    kind="identity.persona",
                    suggested_canonical_kind="identity.persona",
                    surface_name="persona-config",
                    candidate_path_template=".oac/candidates/roblox-embodiment/persona.luau",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Persona config scanned back as identity candidate.",
                ),
                IngestRule(
                    name="memory-config",
                    patterns=(
                        surface_template(profile, "memory-config", "agent-config/memory.luau"),
                    ),
                    kind="memory.semantic",
                    suggested_canonical_kind="memory.semantic",
                    surface_name="memory-config",
                    candidate_path_template=".oac/candidates/roblox-embodiment/memory.luau",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Semantic memory config scanned back as memory candidate.",
                ),
                IngestRule(
                    name="patrol-config",
                    patterns=(
                        surface_template(profile, "patrol-config", "agent-config/patrols.luau"),
                    ),
                    kind="procedure.patrol",
                    suggested_canonical_kind="procedure.patrol",
                    surface_name="patrol-config",
                    candidate_path_template=".oac/candidates/roblox-embodiment/patrols.luau",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Patrol config scanned back as procedure candidates.",
                ),
                IngestRule(
                    name="motion-logs",
                    patterns=("data/motion-logs/*.jsonl",),
                    kind="telemetry.motion",
                    suggested_canonical_kind="telemetry.motion",
                    surface_name="motion-logs",
                    candidate_path_template=".oac/candidates/roblox-embodiment/motion/{stem}.jsonl",
                    parser=ParserKind.JSON,
                    portability=PortabilityClass.RUNTIME_STATE,
                    ownership_mode=OwnershipMode.SIDECAR,
                    notes="Motion log exports from DataStore or in-game telemetry.",
                ),
                IngestRule(
                    name="audit-trail",
                    patterns=("data/audit/*.jsonl",),
                    kind="telemetry.audit",
                    suggested_canonical_kind="telemetry.audit",
                    surface_name="audit-trail",
                    candidate_path_template=".oac/candidates/roblox-embodiment/audit/{stem}.jsonl",
                    parser=ParserKind.JSON,
                    portability=PortabilityClass.RUNTIME_STATE,
                    ownership_mode=OwnershipMode.SIDECAR,
                    notes="Audit trail exports from in-game agent actions.",
                ),
            ],
            notes=[
                "Projection metadata (manifest.json) is ignored during ingest.",
                "Motion and audit logs are runtime-state and stay as sidecars.",
            ],
        )

    def ingest(
        self,
        source_root: Path,
        capsule_root: Path,
        options: AdapterOptions | None = None,
    ) -> IngestReport:
        _ = capsule_root
        plan = self.ingest_plan(options)
        return run_ingest_plan(source_root, plan, options)
