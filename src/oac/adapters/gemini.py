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


class GeminiAdapter:
    """Hydrate a capsule into Gemini CLI surfaces."""

    name = "gemini"
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
                "Settings and extension assets are replaceable sidecars "
                "around the canonical capsule."
            ],
        )

        context_path = destination / surface_path(profile, "context-file", "GEMINI.md")
        agent_root = destination / surface_path(profile, "agent-root", ".gemini/agents")
        settings_path = destination / surface_path(profile, "settings", ".gemini/settings.json")
        extension_root = destination / surface_path(
            profile, "extension-root", ".gemini/extensions/oac"
        )
        imported_root = destination / ".oac/gemini/instructions"

        files = {
            context_path: (
                "# GEMINI.md\n\n"
                "Keep this file concise.\n\n"
                "@.oac/gemini/instructions/project-rules.md\n"
            ),
            imported_root / "project-rules.md": (
                "# project rules\n\n"
                "- Prefer imported markdown fragments over one huge context file.\n"
                "- Keep settings and extension wiring replaceable.\n"
                f"- Capsule: `{capsule.manifest.capsule_id}`\n"
            ),
            agent_root / "reviewer.md": (
                "---\n"
                "name: reviewer\n"
                "description: Reviews starter repository changes.\n"
                "kind: local\n"
                "tools:\n"
                "  - read_file\n"
                "  - grep_search\n"
                "model: gemini-2.5-pro\n"
                "temperature: 0.2\n"
                "max_turns: 10\n"
                "---\n\n"
                "Audit changes for schema drift, fixture drift, and launch honesty.\n"
            ),
            settings_path: (
                "{\n"
                '  "experimental": {\n'
                '    "enableAgents": true\n'
                "  },\n"
                '  "mcpServers": {\n'
                '    "oac": {\n'
                '      "command": "oac",\n'
                '      "args": ["serve-mcp"]\n'
                "    }\n"
                "  }\n"
                "}\n"
            ),
            extension_root
            / "gemini-extension.json": '{\n  "name": "oac-extension",\n  "version": "0.1.0"\n}\n',
            extension_root / "hooks/hooks.json": (
                "{\n"
                '  "postHydrate": [\n'
                "    {\n"
                '      "command": "zig",\n'
                '      "args": ["run", "examples/hooks/zig/post_hydrate_notice.zig"]\n'
                "    }\n"
                "  ]\n"
                "}\n"
            ),
        }

        for path, content in files.items():
            updated = True
            if not options.dry_run:
                if path.suffix == ".json":
                    try:
                        # Attempt to parse and use write_json_if_changed for better JSON handling
                        import json

                        updated = write_json_if_changed(path, json.loads(content))
                    except Exception:
                        updated = write_if_changed(path, content)
                else:
                    updated = write_if_changed(path, content)
            ownership = (
                OwnershipMode.IMPORTED_FILE
                if path.parent == imported_root
                else OwnershipMode.MANAGED_FILE
            )
            record_artifact(
                report, str(path.relative_to(destination)), path.name, ownership, updated=updated
            )

        return report

    def ingest_plan(self, options: AdapterOptions | None = None) -> IngestPlan:
        options = options or AdapterOptions()
        profile = load_effective_profile(self.name, options.profile_path)
        return IngestPlan(
            target=self.name,
            support=IngestSupport.PARTIAL,
            summary=(
                "Scan Gemini root context, imported instructions, agents, settings, and extensions."
            ),
            rules=[
                IngestRule(
                    name="context-file",
                    patterns=(surface_template(profile, "context-file", "GEMINI.md"),),
                    kind="behavior.rule",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="context-file",
                    candidate_path_template=".oac/candidates/gemini/context-file.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="imported-instructions",
                    patterns=(
                        surface_template(
                            profile, "imported-instructions", ".oac/gemini/instructions/*.md"
                        ),
                    ),
                    kind="instruction.fragment",
                    suggested_canonical_kind="behavior.rule",
                    surface_name="imported-instructions",
                    candidate_path_template=".oac/candidates/gemini/instructions/{stem}.md",
                    ownership_mode=OwnershipMode.IMPORTED_FILE,
                ),
                IngestRule(
                    name="agents",
                    patterns=(f"{surface_template(profile, 'agent-root', '.gemini/agents')}/*.md",),
                    kind="agent.specialist",
                    surface_name="agent-root",
                    candidate_path_template=".oac/candidates/gemini/agents/{agent_name}.md",
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="settings",
                    patterns=(surface_template(profile, "settings", ".gemini/settings.json"),),
                    kind="config.signal",
                    surface_name="settings",
                    candidate_path_template=".oac/candidates/gemini/settings.json",
                    parser=ParserKind.JSON,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                ),
                IngestRule(
                    name="extension-manifest",
                    patterns=(
                        f"{surface_template(profile, 'extension-root', '.gemini/extensions/oac')}"
                        "/*.json",
                    ),
                    kind="extension.bundle",
                    surface_name="extension-root",
                    candidate_path_template=".oac/candidates/gemini/extensions/{stem}.json",
                    parser=ParserKind.JSON,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    exclude_names=("hooks.json",),
                ),
                IngestRule(
                    name="hook-bundles",
                    patterns=(
                        f"{surface_template(profile, 'extension-root', '.gemini/extensions/oac')}"
                        "/hooks/*.json",
                    ),
                    kind="hook.bundle",
                    surface_name="extension-root",
                    candidate_path_template=".oac/candidates/gemini/hooks/{stem}.json",
                    parser=ParserKind.JSON,
                    ownership_mode=OwnershipMode.MANAGED_FILE,
                    portability=PortabilityClass.PORTABLE,
                ),
            ],
            notes=[
                "Gemini settings and extensions are scanned as structured signal, "
                "not canonical truth.",
                "Imported markdown is preferred over stuffing the root file indefinitely.",
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
