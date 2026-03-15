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
from oac.capsule import first_sentence, load_capsule
from oac.ingest import IngestPlan, IngestRule, run_ingest_plan
from oac.io import write_if_changed


class QwenCodeAdapter:
    """Hydrate a capsule into a Qwen Code workspace projection.

    Qwen Code is an agent CLI powered by Qwen models. The adapter emits:
    - ``QWEN.md`` — workspace rules, identity, and memory (concise top-level guidance)
    - ``AGENTS.md`` — behavior rules for the agent
    - ``.oac/qwen/`` — imported identity, memory, and projection metadata
    - ``skills/`` — discoverable skill bundles

    Ingest scans Qwen Code workspace files back into typed OAC candidates.
    """

    name = "qwen-code"
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
                "QWEN.md is the primary guidance surface.",
                "Memory records project into workspace memory sidecar.",
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

        # --- QWEN.md (top-level guidance) ---
        qwen_md_path = destination / surface_path(profile, "project-guidance", "QWEN.md")
        qwen_md_text = (
            "# QWEN.md\n\n"
            f"Agent: {identity_name}\n\n"
            "See the following OAC-managed files for context:\n"
            "- `.oac/qwen/persona.md` (Agent Persona)\n"
            "- `.oac/qwen/user-model.md` (User Model)\n"
            "- `.oac/qwen/memory.md` (Curated Memory)\n\n"
            "## Memory\n\n"
            + "\n".join(f"- {item}" for item in memory_bullets)
            + "\n"
        )
        updated = True
        if not options.dry_run:
            updated = write_if_changed(qwen_md_path, qwen_md_text)
        record_artifact(
            report,
            str(qwen_md_path.relative_to(destination)),
            first_sentence(qwen_md_text),
            OwnershipMode.MANAGED_FILE,
            updated=updated,
        )

        # --- AGENTS.md (behavior rules) ---
        agents_md_path = destination / surface_path(
            profile, "behavior-rules", "AGENTS.md"
        )
        agents_md_text = (
            "# AGENTS.md\n\n"
            "## Behavior Rules\n\n"
            "- Keep the workspace concise and durable.\n"
            "- Promote durable learnings back into the capsule.\n"
            f"- Canonical capsule: `{capsule.manifest.capsule_id}`\n"
        )
        updated = True
        if not options.dry_run:
            updated = write_if_changed(agents_md_path, agents_md_text)
        record_artifact(
            report,
            str(agents_md_path.relative_to(destination)),
            first_sentence(agents_md_text),
            OwnershipMode.MANAGED_FILE,
            updated=updated,
        )

        # --- Imported identity files ---
        persona_path = destination / surface_path(
            profile, "persona", ".oac/qwen/persona.md"
        )
        persona_text = f"# Persona\n\n{persona_body}\n"
        updated = True
        if not options.dry_run:
            updated = write_if_changed(persona_path, persona_text)
        record_artifact(
            report,
            str(persona_path.relative_to(destination)),
            first_sentence(persona_text),
            OwnershipMode.IMPORTED_FILE,
            updated=updated,
        )

        user_model_path = destination / surface_path(
            profile, "user-model", ".oac/qwen/user-model.md"
        )
        user_model_text = f"# User Model\n\n{user_body}\n"
        updated = True
        if not options.dry_run:
            updated = write_if_changed(user_model_path, user_model_text)
        record_artifact(
            report,
            str(user_model_path.relative_to(destination)),
            first_sentence(user_model_text),
            OwnershipMode.IMPORTED_FILE,
            updated=updated,
        )

        identity_path = destination / surface_path(
            profile, "display-identity", ".oac/qwen/identity.md"
        )
        identity_text = f"# Identity\n\n{identity_name}\n"
        updated = True
        if not options.dry_run:
            updated = write_if_changed(identity_path, identity_text)
        record_artifact(
            report,
            str(identity_path.relative_to(destination)),
            first_sentence(identity_text),
            OwnershipMode.IMPORTED_FILE,
            updated=updated,
        )

        # --- Curated memory sidecar ---
        memory_path = destination / surface_path(
            profile, "curated-memory", ".oac/qwen/memory.md"
        )
        memory_text = (
            "# Memory\n\n"
            + "\n".join(f"- {item}" for item in memory_bullets)
            + "\n"
        )
        updated = True
        if not options.dry_run:
            updated = write_if_changed(memory_path, memory_text)
        record_artifact(
            report,
            str(memory_path.relative_to(destination)),
            first_sentence(memory_text),
            OwnershipMode.SIDECAR,
            updated=updated,
        )

        # --- Skills ---
        skill_root = surface_path(profile, "skill-root", "skills")
        for skill in capsule.skills:
            skill_path = destination / skill_root / skill.name / "SKILL.md"
            updated = True
            if not options.dry_run:
                updated = write_if_changed(skill_path, skill.content)
            record_artifact(
                report,
                str(skill_path.relative_to(destination)),
                f"Projected Qwen Code skill: {skill.name}",
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        # --- Projection metadata ---
        metadata_path = destination / ".oac/qwen/projection.json"
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
            "Qwen Code projection metadata.",
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
            summary="Scan Qwen Code workspace files back into typed candidate bundles.",
            rules=[
                IngestRule(
                    name="project-guidance",
                    patterns=(surface_template(profile, "project-guidance", "QWEN.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="project-guidance",
                    candidate_path_template=".oac/candidates/qwen-code/project-guidance.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="behavior-rules",
                    patterns=(surface_template(profile, "behavior-rules", "AGENTS.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="behavior-rules",
                    candidate_path_template=".oac/candidates/qwen-code/behavior-rules.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="persona",
                    patterns=(
                        surface_template(profile, "persona", ".oac/qwen/persona.md"),
                    ),
                    kind="identity.persona",
                    suggested_canonical_kind="identity.persona",
                    surface_name="persona",
                    candidate_path_template=".oac/candidates/qwen-code/persona.md",
                    ownership_mode=OwnershipMode.IMPORTED_FILE,
                ),
                IngestRule(
                    name="user-model",
                    patterns=(
                        surface_template(profile, "user-model", ".oac/qwen/user-model.md"),
                    ),
                    kind="user.model",
                    suggested_canonical_kind="user.model",
                    surface_name="user-model",
                    candidate_path_template=".oac/candidates/qwen-code/user-model.md",
                    ownership_mode=OwnershipMode.IMPORTED_FILE,
                ),
                IngestRule(
                    name="display-identity",
                    patterns=(
                        surface_template(
                            profile, "display-identity", ".oac/qwen/identity.md"
                        ),
                    ),
                    kind="identity.display",
                    suggested_canonical_kind="identity.display",
                    surface_name="display-identity",
                    candidate_path_template=".oac/candidates/qwen-code/display-identity.md",
                    ownership_mode=OwnershipMode.IMPORTED_FILE,
                ),
                IngestRule(
                    name="curated-memory",
                    patterns=(
                        surface_template(
                            profile, "curated-memory", ".oac/qwen/memory.md"
                        ),
                    ),
                    kind="memory.semantic",
                    suggested_canonical_kind="memory.semantic",
                    surface_name="curated-memory",
                    candidate_path_template=".oac/candidates/qwen-code/curated-memory.md",
                    portability=PortabilityClass.USER_LOCAL,
                    ownership_mode=OwnershipMode.SIDECAR,
                    notes="Curated memory is machine-local and should promote deliberately.",
                ),
                IngestRule(
                    name="skills",
                    patterns=(
                        f"{surface_template(profile, 'skill-root', 'skills')}/*/SKILL.md",
                    ),
                    kind="procedure.workflow",
                    suggested_canonical_kind="procedure.workflow",
                    surface_name="skill-root",
                    candidate_path_template=".oac/candidates/qwen-code/skills/{skill_name}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
            ],
            notes=[
                "Projection metadata is excluded from ingest.",
                "Curated memory is user-local by default and requires explicit promotion.",
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
