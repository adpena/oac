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


class OpenCodeAdapter:
    """Hydrate a capsule into an OpenCode-shaped project."""

    name = "opencode"
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
            notes=["Agent, command, and plugin files are starter examples, not full integrations."],
        )

        agents_path = destination / surface_path(profile, "project-rules", "AGENTS.md")
        guidance_path = destination / ".oac/opencode/project-guidance.md"
        command_root = destination / surface_path(profile, "command-root", ".opencode/commands")
        agent_root = destination / surface_path(profile, "agent-root", ".opencode/agents")
        plugin_root = destination / surface_path(profile, "plugin-root", ".opencode/plugins")
        config_path = destination / surface_path(profile, "config", "opencode.jsonc")
        skill_root = destination / surface_path(profile, "skill-root", ".agents/skills")

        files = {
            agents_path: (
                "# AGENTS.md\n\n"
                "<!-- BEGIN OAC GENERATED:opencode -->\n"
                "Use shared skills from `.agents/skills/` and specialized agents from "
                "`.opencode/agents/`.\n"
                "<!-- END OAC GENERATED:opencode -->\n"
            ),
            guidance_path: (
                "# project guidance\n\nKeep generated and human-authored instructions distinct.\n"
            ),
            agent_root / "reviewer.md": (
                "---\n"
                "name: reviewer\n"
                "description: Reviews changes against starter contracts.\n"
                "mode: subagent\n"
                "---\n\n"
                "Focus on contract drift, tests, and launch honesty.\n"
            ),
            command_root / "review.md": (
                "---\n"
                "description: Review launch-facing artifacts\n"
                "agent: reviewer\n"
                "---\n\n"
                "Review the changed docs, profiles, and fixtures.\n"
            ),
            plugin_root / "oac-hooks.ts": (
                "export default {\n"
                '  name: "oac-hooks",\n'
                "  setup() {\n"
                "    // starter plugin placeholder for advanced hook/callback logic\n"
                "  },\n"
                "};\n"
            ),
            config_path: (
                "{\n"
                '  "$schema": "https://opencode.ai/config.json",\n'
                '  "instructions": ["AGENTS.md", ".oac/opencode/project-guidance.md"],\n'
                '  "plugin": ["./.opencode/plugins/oac-hooks.ts"],\n'
                '  "mcp": {\n'
                '    "oac": {\n'
                '      "enabled": true\n'
                "    }\n"
                "  }\n"
                "}\n"
            ),
        }

        for path, content in files.items():
            updated = True
            if not options.dry_run:
                if path.suffix == ".json" or path.suffix == ".jsonc":
                    # opencode.jsonc is actually just json for OAC's purposes
                    try:
                        import json

                        updated = write_json_if_changed(path, json.loads(content))
                    except Exception:
                        updated = write_if_changed(path, content)
                else:
                    updated = write_if_changed(path, content)
            ownership = (
                self.default_ownership_mode if path == agents_path else OwnershipMode.MANAGED_FILE
            )
            record_artifact(
                report, str(path.relative_to(destination)), path.name, ownership, updated=updated
            )

        for skill in capsule.skills:
            skill_path = destination / skill_root / skill.name / "SKILL.md"
            updated = True
            if not options.dry_run:
                updated = write_if_changed(skill_path, skill.content)
            record_artifact(
                report,
                str(skill_path.relative_to(destination)),
                f"Projected OpenCode skill: {skill.name}",
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
            summary=(
                "Scan OpenCode rules, skills, agents, commands, plugins, and config "
                "into candidates."
            ),
            rules=[
                IngestRule(
                    name="project-rules",
                    patterns=(surface_template(profile, "project-rules", "AGENTS.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="project-rules",
                    candidate_path_template=".oac/candidates/opencode/project-rules.md",
                    parser=ParserKind.MANAGED_SECTION,
                    ownership_mode=OwnershipMode.MANAGED_SECTION,
                    managed_section_tag="opencode",
                ),
                IngestRule(
                    name="project-guidance",
                    patterns=(".oac/opencode/project-guidance.md",),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="project-guidance",
                    candidate_path_template=".oac/candidates/opencode/project-guidance.md",
                    ownership_mode=OwnershipMode.IMPORTED_FILE,
                ),
                IngestRule(
                    name="skills",
                    patterns=(
                        f"{surface_template(profile, 'skill-root', '.agents/skills')}/*/SKILL.md",
                    ),
                    kind="procedure.workflow",
                    suggested_canonical_kind="procedure.workflow",
                    surface_name="skill-root",
                    candidate_path_template=".oac/candidates/opencode/skills/{skill_name}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="agents",
                    patterns=(
                        f"{surface_template(profile, 'agent-root', '.opencode/agents')}/*.md",
                    ),
                    kind="agent.specialist",
                    surface_name="agent-root",
                    candidate_path_template=".oac/candidates/opencode/agents/{agent_name}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="commands",
                    patterns=(
                        f"{surface_template(profile, 'command-root', '.opencode/commands')}/*.md",
                    ),
                    kind="command.template",
                    surface_name="command-root",
                    candidate_path_template=".oac/candidates/opencode/commands/{command_name}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="plugin-hooks",
                    patterns=(
                        f"{surface_template(profile, 'plugin-root', '.opencode/plugins')}/*.ts",
                    ),
                    kind="hook.logic",
                    surface_name="plugin-root",
                    candidate_path_template=".oac/candidates/opencode/plugins/{plugin_name}.ts",
                    portability=PortabilityClass.PORTABLE,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    notes="Plugin logic may remain target-specific even when reviewed in OAC.",
                ),
                IngestRule(
                    name="config",
                    patterns=(surface_template(profile, "config", "opencode.jsonc"),),
                    kind="config.signal",
                    surface_name="config",
                    candidate_path_template=".oac/candidates/opencode/config.json",
                    parser=ParserKind.JSON,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
            ],
            notes=[
                "OpenCode-specific agents, commands, and plugin hooks may stay "
                "target-local after review.",
                "Config is scanned as signal, not promoted blindly into canonical memory.",
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
