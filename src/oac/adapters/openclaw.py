from __future__ import annotations

from pathlib import Path

from oac.adapter_utils import (
    load_effective_profile,
    record_artifact,
    surface_path,
    surface_template,
    template_to_glob,
    write_json_if_changed,
)
from oac.adapters.base import (
    AdapterOptions,
    IngestReport,
    IngestSupport,
    LossinessKind,
    OwnershipMode,
    ProjectionReport,
)
from oac.capsule import first_sentence, load_capsule
from oac.ingest import IngestPlan, IngestRule, run_ingest_plan
from oac.io import write_if_changed


class OpenClawAdapter:
    """Hydrate a capsule into an OpenClaw workspace projection."""

    name = "openclaw"
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
            notes=[
                "Workspace projection is portable.",
                "Auth, sessions, and runtime state are intentionally out of scope.",
            ],
        )

        persona_body = (
            capsule.persona.body if capsule.persona else "Prefer concrete, testable changes."
        )
        user_body = capsule.user_model.body if capsule.user_model else "Keep the design practical."
        identity_name = capsule.manifest.name
        memory_bullets = capsule.semantic_bullets()[:6]
        if not memory_bullets:
            memory_bullets = [
                "OAC is canonical.",
                "Promote durable learnings deliberately.",
            ]

        files = {
            surface_path(
                profile, "workspace-rules", "AGENTS.md"
            ): "# OpenClaw Rules\n\nKeep the workspace concise and durable.\n",
            surface_path(profile, "persona", "SOUL.md"): f"# Soul\n\n{persona_body}\n",
            surface_path(profile, "user-model", "USER.md"): f"# User\n\n{user_body}\n",
            surface_path(
                profile, "display-identity", "IDENTITY.md"
            ): f"# Identity\n\n{identity_name}\n",
            surface_path(
                profile, "tool-notes", "TOOLS.md"
            ): "# Tools\n\nPrefer deterministic automation and explicit wrappers.\n",
            surface_path(profile, "curated-memory", "MEMORY.md"): "# Memory\n\n"
            + "\n".join(f"- {item}" for item in memory_bullets)
            + "\n",
            surface_path(
                profile, "episodic-memory", "memory/{date}.md", date="2026-03-12"
            ): f"# 2026-03-12\n\nHydrated from capsule `{capsule.manifest.capsule_id}`.\n",
        }

        for rel_path, content in files.items():
            path = destination / rel_path
            updated = True
            if not options.dry_run:
                updated = write_if_changed(path, content)
            record_artifact(
                report,
                rel_path,
                first_sentence(content),
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        skill_root = surface_path(profile, "skill-root", "skills")
        for skill in capsule.skills:
            skill_path = destination / skill_root / skill.name / "SKILL.md"
            updated = True
            if not options.dry_run:
                updated = write_if_changed(skill_path, skill.content)
            record_artifact(
                report,
                str(skill_path.relative_to(destination)),
                f"Projected OpenClaw skill: {skill.name}",
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        metadata_path = destination / ".oac/openclaw/projection.json"
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
            "OpenClaw projection metadata.",
            OwnershipMode.MANAGED_FILE,
            updated=updated,
        )

        return report

    def ingest_plan(self, options: AdapterOptions | None = None) -> IngestPlan:
        options = options or AdapterOptions()
        profile = load_effective_profile(self.name, options.profile_path)
        return IngestPlan(
            target=self.name,
            support=IngestSupport.PARTIAL,
            summary="Scan portable OpenClaw workspace files back into typed candidate bundles.",
            rules=[
                IngestRule(
                    name="workspace-rules",
                    patterns=(surface_template(profile, "workspace-rules", "AGENTS.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="workspace-rules",
                    candidate_path_template=".oac/candidates/openclaw/workspace-rules.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="persona",
                    patterns=(surface_template(profile, "persona", "SOUL.md"),),
                    kind="identity.persona",
                    suggested_canonical_kind="identity.persona",
                    surface_name="persona",
                    candidate_path_template=".oac/candidates/openclaw/persona.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="user-model",
                    patterns=(surface_template(profile, "user-model", "USER.md"),),
                    kind="user.model",
                    suggested_canonical_kind="user.model",
                    surface_name="user-model",
                    candidate_path_template=".oac/candidates/openclaw/user-model.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="display-identity",
                    patterns=(surface_template(profile, "display-identity", "IDENTITY.md"),),
                    kind="identity.display",
                    suggested_canonical_kind="identity.display",
                    surface_name="display-identity",
                    candidate_path_template=".oac/candidates/openclaw/display-identity.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="tool-notes",
                    patterns=(surface_template(profile, "tool-notes", "TOOLS.md"),),
                    kind="tool.note",
                    surface_name="tool-notes",
                    candidate_path_template=".oac/candidates/openclaw/tool-notes.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="curated-memory",
                    patterns=(surface_template(profile, "curated-memory", "MEMORY.md"),),
                    kind="memory.semantic",
                    suggested_canonical_kind="memory.semantic",
                    surface_name="curated-memory",
                    candidate_path_template=".oac/candidates/openclaw/curated-memory.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="episodic-memory",
                    patterns=(
                        template_to_glob(
                            surface_template(profile, "episodic-memory", "memory/{date}.md")
                        ),
                    ),
                    kind="memory.episodic",
                    surface_name="episodic-memory",
                    candidate_path_template=".oac/candidates/openclaw/episodic/{stem}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Episodic daily logs may later summarize into durable memory.",
                ),
                IngestRule(
                    name="skills",
                    patterns=(f"{surface_template(profile, 'skill-root', 'skills')}/*/SKILL.md",),
                    kind="procedure.workflow",
                    suggested_canonical_kind="procedure.workflow",
                    surface_name="skill-root",
                    candidate_path_template=".oac/candidates/openclaw/skills/{skill_name}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
            ],
            notes=[
                "The runtime sidecar is intentionally excluded from ingest.",
                "Workspace files are treated as portable, but promotion remains explicit.",
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
