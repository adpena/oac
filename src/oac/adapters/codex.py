from __future__ import annotations

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


class CodexAdapter:
    """Hydrate a capsule into a Codex-shaped repository."""

    name = "codex"
    default_ownership_mode = OwnershipMode.MANAGED_SECTION

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
            notes=["Deep memory stays outside AGENTS.md and loads on demand."],
        )

        agents_path = destination / surface_path(profile, "project-rules", "AGENTS.md")
        agents_text = (
            "# AGENTS.md\n\n"
            "<!-- BEGIN OAC GENERATED:codex -->\n"
            "## Open Agent Capsule projection\n\n"
            f"- Canonical capsule: `{capsule.manifest.capsule_id}`\n"
            "- Use `.agents/skills/` for durable workflows.\n"
            "- Keep deep memory outside this file and access it via `.oac/codex/` or MCP.\n"
            "<!-- END OAC GENERATED:codex -->\n"
        )
        updated = True
        if not options.dry_run:
            updated = write_if_changed(agents_path, agents_text)
        record_artifact(
            report,
            str(agents_path.relative_to(destination)),
            "Codex guidance surface.",
            self.default_ownership_mode,
            updated=updated,
        )

        identity_root = surface_path(profile, "identity", ".oac/codex/identity")
        identity_map = {
            "identity": (capsule.display_identity, "identity.display"),
            "persona": (capsule.persona, "identity.persona"),
            "user-model": (capsule.user_model, "user.model"),
        }
        for slug, (record, kind) in identity_map.items():
            if not record:
                continue
            path = destination / identity_root / f"{slug}.md"
            updated = True
            if not options.dry_run:
                updated = write_if_changed(path, record.body)
            record_artifact(
                report,
                str(path.relative_to(destination)),
                f"Projected {kind}: {slug}",
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        memory_root = surface_path(profile, "memory-root", ".oac/codex/memory")
        for record in capsule.semantic_memory:
            slug = record.path.stem
            memory_path = destination / memory_root / f"{slug}.md"
            updated = True
            if not options.dry_run:
                updated = write_if_changed(memory_path, record.body)
            record_artifact(
                report,
                str(memory_path.relative_to(destination)),
                f"Projected semantic memory: {slug}",
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        skill_root = surface_path(profile, "skill-root", ".agents/skills")
        for skill in capsule.skills:
            skill_path = destination / skill_root / skill.name / "SKILL.md"
            updated = True
            if not options.dry_run:
                updated = write_if_changed(skill_path, skill.content)
            record_artifact(
                report,
                str(skill_path.relative_to(destination)),
                f"Projected skill bundle: {skill.name}",
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        metadata_path = destination / surface_path(
            profile,
            "projection-metadata",
            ".oac/codex/projection.json",
        )
        updated = True
        if not options.dry_run:
            updated = write_json_if_changed(
                metadata_path,
                {
                    "target": self.name,
                    "capsule_id": capsule.manifest.capsule_id,
                    "profile": profile.profile_name,
                },
            )
        record_artifact(
            report,
            str(metadata_path.relative_to(destination)),
            "Traceability metadata for the Codex projection.",
            OwnershipMode.MANAGED_FILE,
            updated=updated,
        )

        return report

    def ingest_plan(self, options: AdapterOptions | None = None) -> IngestPlan:
        options = options or AdapterOptions()
        profile = load_effective_profile(self.name, options.profile_path)
        id_root = surface_template(profile, "identity", ".oac/codex/identity")
        return IngestPlan(
            target=self.name,
            support=IngestSupport.PARTIAL,
            summary="Scan Codex guidance and skills back into typed candidate bundles.",
            rules=[
                IngestRule(
                    name="project-rules",
                    patterns=(surface_template(profile, "project-rules", "AGENTS.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="project-rules",
                    candidate_path_template=".oac/candidates/codex/project-rules.md",
                    parser=ParserKind.MANAGED_SECTION,
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_SECTION,
                    managed_section_tag="codex",
                    notes="Codex durable rules should stay concise and reviewable.",
                ),
                IngestRule(
                    name="skills",
                    patterns=(
                        f"{surface_template(profile, 'skill-root', '.agents/skills')}/*/SKILL.md",
                    ),
                    kind="procedure.workflow",
                    suggested_canonical_kind="procedure.workflow",
                    surface_name="skill-root",
                    candidate_path_template=".oac/candidates/codex/skills/{skill_name}.md",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Codex skills are promoted as durable workflow candidates.",
                ),
                IngestRule(
                    name="identity-display",
                    patterns=(f"{id_root}/identity.md",),
                    kind="identity.display",
                    suggested_canonical_kind="identity.display",
                    surface_name="identity",
                    candidate_path_template=".oac/candidates/codex/identity/identity.md",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Identity display updates from Codex.",
                ),
                IngestRule(
                    name="identity-persona",
                    patterns=(f"{id_root}/persona.md",),
                    kind="identity.persona",
                    suggested_canonical_kind="identity.persona",
                    surface_name="identity",
                    candidate_path_template=".oac/candidates/codex/identity/persona.md",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Persona updates from Codex.",
                ),
                IngestRule(
                    name="identity-user-model",
                    patterns=(f"{id_root}/user-model.md",),
                    kind="user.model",
                    suggested_canonical_kind="user.model",
                    surface_name="identity",
                    candidate_path_template=".oac/candidates/codex/identity/user-model.md",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="User model updates from Codex.",
                ),
                IngestRule(
                    name="memory",
                    patterns=(
                        f"{surface_template(profile, 'memory-root', '.oac/codex/memory')}/*.md",
                    ),
                    kind="memory.semantic",
                    suggested_canonical_kind="memory.semantic",
                    surface_name="memory-root",
                    candidate_path_template=".oac/candidates/codex/memory/{stem}.md",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Semantic memory edits are promoted as portable memory candidates.",
                ),
            ],
            notes=[
                "Projection metadata is ignored during ingest.",
                "Deep memory remains a future add-on via local files or MCP.",
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
