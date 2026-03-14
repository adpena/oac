from __future__ import annotations

from pathlib import Path

from oac.adapter_utils import (
    load_effective_profile,
    record_artifact,
    surface_path,
    surface_template,
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
from oac.ingest import IngestPlan, IngestRule, run_ingest_plan
from oac.io import write_text


class ClaudeCodeAdapter:
    """Hydrate a capsule into Claude Code guidance plus local memory topics.

    The starter keeps ``CLAUDE.md`` concise and treats ``memory/MEMORY.md`` as an index,
    not as a giant dump of every canonical record.
    """

    name = "claude-code"
    default_ownership_mode = OwnershipMode.IMPORTED_FILE

    def hydrate(
        self,
        capsule_root: Path,
        destination: Path,
        options: AdapterOptions | None = None,
    ) -> ProjectionReport:
        options = options or AdapterOptions()
        capsule = load_capsule(capsule_root)
        profile = load_effective_profile(self.name, options.profile_path)

        report = ProjectionReport(
            target=self.name,
            destination=str(destination),
            ownership_mode=self.default_ownership_mode,
            lossiness=LossinessKind.PARTIALLY_LOSSLESS,
            notes=[
                "CLAUDE.md is kept concise.",
                "Auto-memory topics are treated as sidecars.",
            ],
        )

        project_guidance_path = destination / surface_path(
            profile,
            "project-guidance",
            "CLAUDE.md",
        )
        imported_guidance_path = destination / surface_path(
            profile,
            "imported-guidance",
            ".oac/claude/project-guidance.md",
        )
        memory_index_path = destination / surface_path(
            profile,
            "memory-index",
            "memory/MEMORY.md",
        )
        preferences_path = destination / "memory/preferences.md"
        architecture_path = destination / "memory/architecture.md"

        all_bullets = capsule.semantic_bullets()
        architecture_bullets = all_bullets[:3] or ["Keep shared guidance explicit and portable."]
        preference_bullets = all_bullets[3:6] or ["Keep memory concise and topic-oriented."]

        files = {
            project_guidance_path: (
                "# CLAUDE.md\n\n"
                "See `.oac/claude/project-guidance.md` for the OAC-managed shared guidance.\n"
            ),
            imported_guidance_path: (
                "# Project guidance\n\n"
                "- Keep MEMORY.md concise.\n"
                "- Promote durable learnings back into the capsule.\n"
                f"- Capsule: `{capsule.manifest.capsule_id}`\n"
            ),
            memory_index_path: (
                "# MEMORY.md\n\n"
                "- architecture -> `architecture.md`\n"
                "- preferences -> `preferences.md`\n"
            ),
            architecture_path: (
                "# architecture\n\n"
                + "\n".join(f"- {item}" for item in architecture_bullets)
                + "\n"
            ),
            preferences_path: (
                "# preferences\n\n" + "\n".join(f"- {item}" for item in preference_bullets) + "\n"
            ),
        }

        for path, content in files.items():
            if not options.dry_run:
                write_text(path, content)
            if path == imported_guidance_path:
                ownership = OwnershipMode.IMPORTED_FILE
            elif path.name == "MEMORY.md" or path.parent.name == "memory":
                ownership = OwnershipMode.SIDECAR
            else:
                ownership = OwnershipMode.MANAGED_SECTION
            record_artifact(report, str(path.relative_to(destination)), path.name, ownership)

        return report

    def ingest_plan(self, options: AdapterOptions | None = None) -> IngestPlan:
        options = options or AdapterOptions()
        profile = load_effective_profile(self.name, options.profile_path)
        return IngestPlan(
            target=self.name,
            support=IngestSupport.PARTIAL,
            summary="Scan Claude Code guidance plus local memory topics into typed candidates.",
            rules=[
                IngestRule(
                    name="project-guidance",
                    patterns=(surface_template(profile, "project-guidance", "CLAUDE.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="project-guidance",
                    candidate_path_template=".oac/candidates/claude-code/project-guidance.md",
                    ownership_mode=OwnershipMode.MANAGED_SECTION,
                    notes="CLAUDE.md is usually a concise shell around imported guidance.",
                ),
                IngestRule(
                    name="imported-guidance",
                    patterns=(
                        surface_template(
                            profile,
                            "imported-guidance",
                            ".oac/claude/project-guidance.md",
                        ),
                    ),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="imported-guidance",
                    candidate_path_template=".oac/candidates/claude-code/imported-guidance.md",
                    ownership_mode=OwnershipMode.IMPORTED_FILE,
                ),
                IngestRule(
                    name="memory-index",
                    patterns=(surface_template(profile, "memory-index", "memory/MEMORY.md"),),
                    kind="memory.index",
                    surface_name="memory-index",
                    candidate_path_template=".oac/candidates/claude-code/memory/index.md",
                    portability=PortabilityClass.USER_LOCAL,
                    ownership_mode=OwnershipMode.SIDECAR,
                ),
                IngestRule(
                    name="memory-topics",
                    patterns=(surface_template(profile, "memory-topics", "memory/*.md"),),
                    kind="memory.semantic",
                    suggested_canonical_kind="memory.semantic",
                    surface_name="memory-topics",
                    candidate_path_template=".oac/candidates/claude-code/memory/{stem}.md",
                    portability=PortabilityClass.USER_LOCAL,
                    ownership_mode=OwnershipMode.SIDECAR,
                    exclude_names=("MEMORY.md",),
                    notes=(
                        "Topic files are machine-local by default and should promote deliberately."
                    ),
                ),
            ],
            notes=[
                "Claude local memory is treated as user-local even when exported for review.",
                "MEMORY.md is an index, so topic files carry most durable signal.",
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
        return run_ingest_plan(source_root, plan)
