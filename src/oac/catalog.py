from __future__ import annotations

from dataclasses import dataclass

import yaml

from oac.adapters.base import OwnershipMode, PortabilityClass
from oac.models import HarnessTarget
from oac.profile_models import (
    AdapterProfile,
    FlagSpec,
    FlagType,
    HookPhase,
    HookRuntime,
    HookSpec,
    MappingMode,
    MappingRule,
    SurfaceSpec,
    WrapperSpec,
)


@dataclass(frozen=True, slots=True)
class TargetCatalogEntry:
    """Public metadata for one supported harness target."""

    target: HarnessTarget
    title: str
    summary: str
    default_profile: AdapterProfile


def _codex_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="codex.default",
        target=HarnessTarget.CODEX,
        description="Default Codex projection with AGENTS.md plus on-demand skills.",
        surfaces=[
            SurfaceSpec(
                name="project-rules",
                path="AGENTS.md",
                ownership_mode=OwnershipMode.MANAGED_SECTION,
                portability=PortabilityClass.PORTABLE,
                notes="Durable repo guidance surface read before work.",
            ),
            SurfaceSpec(
                name="skill-root",
                path=".agents/skills",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Reusable workflows projected as agent skills.",
            ),
            SurfaceSpec(
                name="projection-metadata",
                path=".oac/codex/projection.json",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Traceability metadata for snapshot tests and reviews.",
            ),
        ],
        flags=[
            FlagSpec(
                name="instruction_strategy",
                cli_name="--instruction-strategy",
                harness_name="AGENTS.md",
                type=FlagType.ENUM,
                default="managed-section",
                description="How OAC guidance is embedded into AGENTS.md.",
                example="managed-section",
            ),
            FlagSpec(
                name="managed_section_tag",
                cli_name="--managed-section-tag",
                harness_name="comment-tag",
                type=FlagType.STRING,
                default="OAC:CODEX",
                description="Marker used for deterministic owned regions.",
            ),
            FlagSpec(
                name="emit_skills",
                cli_name="--emit-skills",
                harness_name=".agents/skills",
                type=FlagType.BOOL,
                default=True,
                description="Emit stable workflow bundles as Codex skills.",
            ),
            FlagSpec(
                name="emit_projection_metadata",
                cli_name="--emit-projection-metadata",
                harness_name=".oac/codex/projection.json",
                type=FlagType.BOOL,
                default=True,
                description="Emit traceability metadata alongside the projection.",
            ),
        ],
        mappings=[
            MappingRule(
                canonical_kind="behavior.rule",
                target_surface="project-rules",
                target_path="AGENTS.md",
                mode=MappingMode.MANAGED_SECTION,
                ownership_mode=OwnershipMode.MANAGED_SECTION,
                notes="Portable behavior rules remain concise in AGENTS.md.",
            ),
            MappingRule(
                canonical_kind="procedure.workflow",
                target_surface="skill-root",
                target_path=".agents/skills/{skill_name}/SKILL.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Workflow bundles project into on-demand skills.",
            ),
            MappingRule(
                canonical_kind="memory.semantic",
                target_surface="projection-metadata",
                target_path=".oac/codex/memory/*.md",
                mode=MappingMode.IMPORTED_FILE,
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes="Deep memory stays outside AGENTS.md and loads on demand.",
            ),
        ],
        hooks=[
            HookSpec(
                name="post-hydrate-notice",
                phase=HookPhase.POST_HYDRATE,
                runtime=HookRuntime.PYTHON,
                entrypoint="examples/hooks/python/post_hydrate_notice.py",
                enabled=True,
                notes="Optional example hook for teams that want notifications or indexing.",
            )
        ],
        wrappers=[
            WrapperSpec(
                name="codex-default",
                command=["codex"],
                notes="Replace or extend this wrapper to match local installation details.",
            )
        ],
    )


def _openclaw_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="openclaw.default",
        target=HarnessTarget.OPENCLAW,
        description="Default OpenClaw workspace projection without implicit state cloning.",
        surfaces=[
            SurfaceSpec(
                name="workspace-rules",
                path="AGENTS.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Core OpenClaw workspace rules.",
            ),
            SurfaceSpec(
                name="persona",
                path="SOUL.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Persona and tone projection surface.",
            ),
            SurfaceSpec(
                name="user-model",
                path="USER.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Durable shared user model.",
            ),
            SurfaceSpec(
                name="display-identity",
                path="IDENTITY.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Display-facing identity surface.",
            ),
            SurfaceSpec(
                name="tool-notes",
                path="TOOLS.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Local tool notes and reminders.",
            ),
            SurfaceSpec(
                name="curated-memory",
                path="MEMORY.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Curated durable OpenClaw memory surface.",
            ),
            SurfaceSpec(
                name="episodic-memory",
                path="memory/{date}.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Recent episodic notes as daily logs.",
            ),
            SurfaceSpec(
                name="skill-root",
                path="skills",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Reusable procedures and task skills.",
            ),
            SurfaceSpec(
                name="runtime-sidecar",
                path=".oac/openclaw/state-sidecar/",
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.RUNTIME_STATE,
                notes="Opt-in encrypted runtime sidecar for state migration scenarios.",
            ),
        ],
        flags=[
            FlagSpec(
                name="emit_daily_memory",
                cli_name="--emit-daily-memory",
                harness_name="memory/{date}.md",
                type=FlagType.BOOL,
                default=True,
                description="Emit episodic notes as OpenClaw daily memory files.",
            ),
            FlagSpec(
                name="emit_tools_notes",
                cli_name="--emit-tools-notes",
                harness_name="TOOLS.md",
                type=FlagType.BOOL,
                default=True,
                description="Emit tool notes when the capsule contains them.",
            ),
            FlagSpec(
                name="emit_state_sidecar",
                cli_name="--emit-state-sidecar",
                harness_name=".oac/openclaw/state-sidecar/",
                type=FlagType.BOOL,
                default=False,
                description=(
                    "Never enabled by default; preserves the line between workspace and full clone."
                ),
            ),
            FlagSpec(
                name="state_sidecar_path",
                cli_name="--state-sidecar-path",
                harness_name="runtime-sidecar.path",
                type=FlagType.PATH,
                default=".oac/openclaw/state-sidecar/",
                description="Opt-in location for encrypted runtime sidecar data.",
            ),
        ],
        mappings=[
            MappingRule(
                canonical_kind="identity.persona",
                target_surface="persona",
                target_path="SOUL.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="OpenClaw keeps persona distinct from rule and memory files.",
            ),
            MappingRule(
                canonical_kind="user.model",
                target_surface="user-model",
                target_path="USER.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Shared user model goes to USER.md, not the runtime sidecar.",
            ),
            MappingRule(
                canonical_kind="memory.semantic",
                target_surface="curated-memory",
                target_path="MEMORY.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Durable semantic memory stays curated and compact.",
            ),
            MappingRule(
                canonical_kind="memory.episodic",
                target_surface="episodic-memory",
                target_path="memory/{date}.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Episodic traces project to daily logs and promote later.",
            ),
            MappingRule(
                canonical_kind="runtime.state",
                target_surface="runtime-sidecar",
                target_path=".oac/openclaw/state-sidecar/",
                mode=MappingMode.SIDECAR,
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.RUNTIME_STATE,
                notes=(
                    "Runtime state is sidecar-only and never implied by the workspace projection."
                ),
            ),
        ],
        hooks=[],
        wrappers=[
            WrapperSpec(
                name="openclaw-default",
                command=["openclaw"],
                notes="Wrapper placeholder for local OpenClaw launch commands.",
            )
        ],
    )


def _claude_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="claude-code.default",
        target=HarnessTarget.CLAUDE_CODE,
        description="Default Claude Code projection split between guidance and local auto-memory.",
        surfaces=[
            SurfaceSpec(
                name="project-guidance",
                path="CLAUDE.md",
                ownership_mode=OwnershipMode.MANAGED_SECTION,
                notes="Shared project instructions with a clear OAC-owned region.",
            ),
            SurfaceSpec(
                name="imported-guidance",
                path=".oac/claude/project-guidance.md",
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes="Optional imported guidance file for larger shared instructions.",
            ),
            SurfaceSpec(
                name="memory-index",
                path="memory/MEMORY.md",
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.USER_LOCAL,
                notes="Concise index for machine-local auto-memory topics.",
            ),
            SurfaceSpec(
                name="memory-topics",
                path="memory/*.md",
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.USER_LOCAL,
                notes="Topic files read on demand by Claude Code memory.",
            ),
        ],
        flags=[
            FlagSpec(
                name="guidance_strategy",
                cli_name="--guidance-strategy",
                harness_name="CLAUDE.md",
                type=FlagType.ENUM,
                default="managed-section",
                description=(
                    "Choose managed section or imported-file projection for shared guidance."
                ),
            ),
            FlagSpec(
                name="memory_topic_limit",
                cli_name="--memory-topic-limit",
                harness_name="memory/*.md",
                type=FlagType.INTEGER,
                default=8,
                description="Limit topic fan-out so MEMORY.md stays concise.",
            ),
            FlagSpec(
                name="emit_local_memory_sidecar",
                cli_name="--emit-local-memory-sidecar",
                harness_name="memory/",
                type=FlagType.BOOL,
                default=True,
                description="Emit machine-local memory index and topic files when requested.",
            ),
        ],
        mappings=[
            MappingRule(
                canonical_kind="behavior.rule",
                target_surface="project-guidance",
                target_path="CLAUDE.md",
                mode=MappingMode.MANAGED_SECTION,
                ownership_mode=OwnershipMode.MANAGED_SECTION,
                notes="Stable project behavior belongs in CLAUDE.md, not auto memory.",
            ),
            MappingRule(
                canonical_kind="memory.semantic",
                target_surface="memory-topics",
                target_path="memory/{topic}.md",
                mode=MappingMode.TOPIC_FILES,
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.USER_LOCAL,
                notes="Claude memory is topic-oriented and machine-local by default.",
            ),
            MappingRule(
                canonical_kind="memory.semantic",
                target_surface="memory-index",
                target_path="memory/MEMORY.md",
                mode=MappingMode.INDEX_FILE,
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.USER_LOCAL,
                notes="MEMORY.md stays concise and routes to detailed topic files.",
            ),
        ],
        hooks=[
            HookSpec(
                name="post-ingest-curate-memory",
                phase=HookPhase.POST_INGEST,
                runtime=HookRuntime.PYTHON,
                entrypoint="examples/hooks/python/post_hydrate_notice.py",
                enabled=False,
                notes="Example hook for curating topic files into proposal records.",
            )
        ],
        wrappers=[],
    )


def _opencode_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="opencode.default",
        target=HarnessTarget.OPENCODE,
        description="Default OpenCode projection with AGENTS.md, skills, agents, and plugin hooks.",
        surfaces=[
            SurfaceSpec(
                name="project-rules",
                path="AGENTS.md",
                ownership_mode=OwnershipMode.MANAGED_SECTION,
                notes="Shared rule file understood by OpenCode.",
            ),
            SurfaceSpec(
                name="skill-root",
                path=".agents/skills",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Shared skill layout compatible with agent-skill conventions.",
            ),
            SurfaceSpec(
                name="agent-root",
                path=".opencode/agents",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Specialized agents emitted from capsule slices.",
            ),
            SurfaceSpec(
                name="command-root",
                path=".opencode/commands",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Optional repetitive task commands exposed to OpenCode.",
            ),
            SurfaceSpec(
                name="plugin-root",
                path=".opencode/plugins",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Optional plugin stubs for advanced hooks and callbacks.",
            ),
            SurfaceSpec(
                name="config",
                path="opencode.jsonc",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="OpenCode config sidecar with instructions and MCP wiring.",
            ),
        ],
        flags=[
            FlagSpec(
                name="emit_agents",
                cli_name="--emit-agents",
                harness_name=".opencode/agents",
                type=FlagType.BOOL,
                default=True,
                description="Emit specialized OpenCode agents from capsule slices.",
            ),
            FlagSpec(
                name="emit_commands",
                cli_name="--emit-commands",
                harness_name=".opencode/commands",
                type=FlagType.BOOL,
                default=True,
                description="Emit custom command stubs for repetitive tasks.",
            ),
            FlagSpec(
                name="emit_plugin_stub",
                cli_name="--emit-plugin-stub",
                harness_name=".opencode/plugins",
                type=FlagType.BOOL,
                default=True,
                description="Ship a starter plugin surface for hooks and wrappers.",
            ),
            FlagSpec(
                name="emit_mcp_config",
                cli_name="--emit-mcp-config",
                harness_name="opencode.jsonc:mcp",
                type=FlagType.BOOL,
                default=True,
                description="Wire OAC MCP resources into OpenCode config by default.",
            ),
        ],
        mappings=[
            MappingRule(
                canonical_kind="behavior.rule",
                target_surface="project-rules",
                target_path="AGENTS.md",
                mode=MappingMode.MANAGED_SECTION,
                ownership_mode=OwnershipMode.MANAGED_SECTION,
                notes="OpenCode consumes AGENTS.md directly.",
            ),
            MappingRule(
                canonical_kind="procedure.workflow",
                target_surface="skill-root",
                target_path=".agents/skills/{skill_name}/SKILL.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Portable workflow bundles become shared skills.",
            ),
            MappingRule(
                canonical_kind="skill.bundle",
                target_surface="agent-root",
                target_path=".opencode/agents/{agent_name}.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Capsule slices can also become specialized agents.",
            ),
        ],
        hooks=[
            HookSpec(
                name="opencode-plugin-post-hydrate",
                phase=HookPhase.POST_HYDRATE,
                runtime=HookRuntime.TYPESCRIPT,
                entrypoint="examples/hooks/typescript/post_hydrate_notice.ts",
                enabled=False,
                notes=(
                    "Example callback mirroring OpenCode plugin or command hooks via Node or Bun."
                ),
            )
        ],
        wrappers=[
            WrapperSpec(
                name="opencode-run",
                command=["opencode", "run"],
                notes="Use this as a default wrapper and customize provider/model flags locally.",
            )
        ],
    )


def _gemini_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="gemini.default",
        target=HarnessTarget.GEMINI,
        description=(
            "Default Gemini CLI projection using GEMINI.md, agents, settings, and extensions."
        ),
        surfaces=[
            SurfaceSpec(
                name="context-file",
                path="GEMINI.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Primary hierarchical context file for Gemini CLI.",
            ),
            SurfaceSpec(
                name="imported-instructions",
                path=".oac/gemini/instructions/*.md",
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes="Imported markdown fragments referenced from GEMINI.md.",
            ),
            SurfaceSpec(
                name="agent-root",
                path=".gemini/agents",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Experimental/custom Gemini agents with YAML frontmatter.",
            ),
            SurfaceSpec(
                name="settings",
                path=".gemini/settings.json",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Gemini CLI settings including MCP and agent toggles.",
            ),
            SurfaceSpec(
                name="extension-root",
                path=".gemini/extensions/oac",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Optional extension surface for hooks, commands, and shared agent assets.",
            ),
        ],
        flags=[
            FlagSpec(
                name="context_file_name",
                cli_name="--context-file-name",
                harness_name="GEMINI.md",
                type=FlagType.STRING,
                default="GEMINI.md",
                description="Canonical filename for Gemini instructional memory.",
            ),
            FlagSpec(
                name="use_imports",
                cli_name="--use-imports",
                harness_name="@file imports",
                type=FlagType.BOOL,
                default=True,
                description="Use GEMINI.md imports to keep the root file concise.",
            ),
            FlagSpec(
                name="emit_agents",
                cli_name="--emit-agents",
                harness_name="experimental.enableAgents",
                type=FlagType.BOOL,
                default=True,
                description="Emit Gemini agents and enable them in settings.",
            ),
            FlagSpec(
                name="emit_mcp_servers",
                cli_name="--emit-mcp-servers",
                harness_name="mcpServers",
                type=FlagType.BOOL,
                default=True,
                description="Register OAC resources and tools in Gemini settings.json.",
            ),
            FlagSpec(
                name="memory_refresh_command",
                cli_name="--memory-refresh-command",
                harness_name="/memory refresh",
                type=FlagType.STRING,
                default="/memory refresh",
                description="Document or wrap the refresh command after regeneration.",
            ),
        ],
        mappings=[
            MappingRule(
                canonical_kind="behavior.rule",
                target_surface="context-file",
                target_path="GEMINI.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="High-value instructions stay in the root GEMINI.md with imports for depth.",
            ),
            MappingRule(
                canonical_kind="memory.semantic",
                target_surface="imported-instructions",
                target_path=".oac/gemini/instructions/{topic}.md",
                mode=MappingMode.IMPORTED_FILE,
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes=(
                    "Semantic memory is imported into GEMINI.md rather than inlined indefinitely."
                ),
            ),
            MappingRule(
                canonical_kind="skill.bundle",
                target_surface="agent-root",
                target_path=".gemini/agents/{agent_name}.md",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Capsule slices can become Gemini subagents with frontmatter.",
            ),
        ],
        hooks=[
            HookSpec(
                name="zig-post-hydrate-refresh-hint",
                phase=HookPhase.POST_HYDRATE,
                runtime=HookRuntime.ZIG,
                entrypoint="examples/hooks/zig/post_hydrate_notice.zig",
                enabled=False,
                notes=(
                    "Starter example showing how a tiny Zig helper can emit refresh or sync hints."
                ),
            )
        ],
        wrappers=[
            WrapperSpec(
                name="gemini-default",
                command=["gemini"],
                notes="Use this wrapper and adapt auth or sandbox flags locally.",
            )
        ],
    )


def _mcp_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="mcp.default",
        target=HarnessTarget.MCP,
        description="Read-only MCP surface for manifest, memory, and projection metadata.",
        surfaces=[
            SurfaceSpec(
                name="manifest-resource",
                path="mcp://capsule/manifest",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Read-only manifest resource.",
            ),
            SurfaceSpec(
                name="identity-resource",
                path="mcp://capsule/identity",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Read-only identity summary resource.",
            ),
            SurfaceSpec(
                name="memory-search",
                path="mcp://capsule/tools/search-memory",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Read-only memory search tool.",
            ),
        ],
        flags=[
            FlagSpec(
                name="read_only",
                cli_name="--read-only",
                harness_name="server.readOnly",
                type=FlagType.BOOL,
                default=True,
                description="Read-only by default until governance for mutation exists.",
            )
        ],
        mappings=[
            MappingRule(
                canonical_kind="provenance.record",
                target_surface="manifest-resource",
                target_path="mcp://capsule/manifest",
                mode=MappingMode.RESOURCE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="MCP exposes metadata but not mutating state.",
            )
        ],
        hooks=[],
        wrappers=[],
    )


def _webmcp_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="webmcp.default",
        target=HarnessTarget.WEBMCP,
        description="Browser-facing read-only WebMCP companion surface.",
        surfaces=[
            SurfaceSpec(
                name="capsule-summary",
                path="webmcp://capsule/summary",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Browser-readable capsule summary surface.",
            ),
            SurfaceSpec(
                name="search-memory",
                path="webmcp://capsule/tools/search-memory",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Read-only browser-invocable search tool.",
            ),
        ],
        flags=[
            FlagSpec(
                name="read_only",
                cli_name="--read-only",
                harness_name="webmcp.readOnly",
                type=FlagType.BOOL,
                default=True,
                description="Keep the launch WebMCP surface strictly read-only.",
            )
        ],
        mappings=[],
        hooks=[],
        wrappers=[],
    )


def _qwen_code_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="qwen-code.default",
        target=HarnessTarget.QWEN_CODE,
        description="Default Qwen Code workspace projection with QWEN.md and memory sidecar.",
        surfaces=[
            SurfaceSpec(
                name="project-guidance",
                path="QWEN.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Primary workspace guidance surface read by Qwen Code.",
            ),
            SurfaceSpec(
                name="behavior-rules",
                path="AGENTS.md",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Behavior rules for agent conduct.",
            ),
            SurfaceSpec(
                name="persona",
                path=".oac/qwen/persona.md",
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes="Persona projection from capsule identity.",
            ),
            SurfaceSpec(
                name="user-model",
                path=".oac/qwen/user-model.md",
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes="User model projection from capsule identity.",
            ),
            SurfaceSpec(
                name="display-identity",
                path=".oac/qwen/identity.md",
                ownership_mode=OwnershipMode.IMPORTED_FILE,
                notes="Display identity projection.",
            ),
            SurfaceSpec(
                name="curated-memory",
                path=".oac/qwen/memory.md",
                ownership_mode=OwnershipMode.SIDECAR,
                portability=PortabilityClass.USER_LOCAL,
                notes="Curated memory sidecar for workspace knowledge.",
            ),
            SurfaceSpec(
                name="skill-root",
                path="skills",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Discoverable skill bundles.",
            ),
        ],
        flags=[],
        mappings=[],
        hooks=[],
        wrappers=[],
    )


def _roblox_embodiment_profile() -> AdapterProfile:
    return AdapterProfile(
        profile_name="roblox-embodiment.default",
        target=HarnessTarget.ROBLOX_EMBODIMENT,
        description="Default Roblox embodiment projection with Luau agent-config tables.",
        surfaces=[
            SurfaceSpec(
                name="skills-config",
                path="agent-config/skills.luau",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Skill definitions as a Luau table literal.",
            ),
            SurfaceSpec(
                name="persona-config",
                path="agent-config/persona.luau",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Agent personality and identity config as Luau table.",
            ),
            SurfaceSpec(
                name="memory-config",
                path="agent-config/memory.luau",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Semantic memory snapshot as Luau table.",
            ),
            SurfaceSpec(
                name="patrol-config",
                path="agent-config/patrols.luau",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Patrol waypoints derived from capsule procedures.",
            ),
            SurfaceSpec(
                name="projection-metadata",
                path="agent-config/manifest.json",
                ownership_mode=OwnershipMode.MANAGED_FILE,
                portability=PortabilityClass.PORTABLE,
                notes="Traceability metadata for the Roblox embodiment projection.",
            ),
        ],
        flags=[
            FlagSpec(
                name="emit_patrol_config",
                cli_name="--emit-patrol-config",
                harness_name="agent-config/patrols.luau",
                type=FlagType.BOOL,
                default=True,
                description="Emit patrol waypoint config from capsule procedures.",
            ),
            FlagSpec(
                name="emit_memory_snapshot",
                cli_name="--emit-memory-snapshot",
                harness_name="agent-config/memory.luau",
                type=FlagType.BOOL,
                default=True,
                description="Emit semantic memory snapshot as a Luau table.",
            ),
            FlagSpec(
                name="luau_strict_mode",
                cli_name="--luau-strict-mode",
                harness_name="luau.strict",
                type=FlagType.BOOL,
                default=True,
                description="Emit --!strict directive at the top of generated Luau files.",
            ),
        ],
        mappings=[
            MappingRule(
                canonical_kind="skill.bundle",
                target_surface="skills-config",
                target_path="agent-config/skills.luau",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Capsule skills project into a single Luau table.",
            ),
            MappingRule(
                canonical_kind="identity.persona",
                target_surface="persona-config",
                target_path="agent-config/persona.luau",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Persona and identity project into agent personality config.",
            ),
            MappingRule(
                canonical_kind="memory.semantic",
                target_surface="memory-config",
                target_path="agent-config/memory.luau",
                mode=MappingMode.MANAGED_FILE,
                ownership_mode=OwnershipMode.MANAGED_FILE,
                notes="Semantic memory projects into a Luau lookup table.",
            ),
        ],
        hooks=[],
        wrappers=[],
    )


CATALOG: dict[HarnessTarget, TargetCatalogEntry] = {
    HarnessTarget.CODEX: TargetCatalogEntry(
        target=HarnessTarget.CODEX,
        title="Codex",
        summary="AGENTS.md plus .agents/skills projection.",
        default_profile=_codex_profile(),
    ),
    HarnessTarget.OPENCLAW: TargetCatalogEntry(
        target=HarnessTarget.OPENCLAW,
        title="OpenClaw",
        summary="Workspace-native markdown brain projection with optional state sidecar.",
        default_profile=_openclaw_profile(),
    ),
    HarnessTarget.CLAUDE_CODE: TargetCatalogEntry(
        target=HarnessTarget.CLAUDE_CODE,
        title="Claude Code",
        summary="Shared project guidance plus local auto-memory sidecar.",
        default_profile=_claude_profile(),
    ),
    HarnessTarget.OPENCODE: TargetCatalogEntry(
        target=HarnessTarget.OPENCODE,
        title="OpenCode",
        summary="AGENTS.md, skills, agents, commands, and plugin-ready config.",
        default_profile=_opencode_profile(),
    ),
    HarnessTarget.GEMINI: TargetCatalogEntry(
        target=HarnessTarget.GEMINI,
        title="Gemini CLI",
        summary="GEMINI.md, imports, agents, settings, and extension-ready surfaces.",
        default_profile=_gemini_profile(),
    ),
    HarnessTarget.MCP: TargetCatalogEntry(
        target=HarnessTarget.MCP,
        title="MCP",
        summary="Read-only access surface for capsule metadata and memory search.",
        default_profile=_mcp_profile(),
    ),
    HarnessTarget.QWEN_CODE: TargetCatalogEntry(
        target=HarnessTarget.QWEN_CODE,
        title="Qwen Code",
        summary="QWEN.md workspace guidance with memory sidecar and discoverable skills.",
        default_profile=_qwen_code_profile(),
    ),
    HarnessTarget.WEBMCP: TargetCatalogEntry(
        target=HarnessTarget.WEBMCP,
        title="WebMCP",
        summary="Browser-facing read-only companion surface.",
        default_profile=_webmcp_profile(),
    ),
    HarnessTarget.ROBLOX_EMBODIMENT: TargetCatalogEntry(
        target=HarnessTarget.ROBLOX_EMBODIMENT,
        title="Roblox Embodiment",
        summary="Luau agent-config projection for embodied Roblox agents.",
        default_profile=_roblox_embodiment_profile(),
    ),
}


def parse_target(value: HarnessTarget | str) -> HarnessTarget:
    """Normalize a target enum or string into a known target."""

    if isinstance(value, HarnessTarget):
        return value
    return HarnessTarget(value)


def list_targets() -> list[TargetCatalogEntry]:
    """Return catalog entries in declaration order."""

    return list(CATALOG.values())


def get_target(value: HarnessTarget | str) -> TargetCatalogEntry:
    """Look up one catalog entry."""

    target = parse_target(value)
    return CATALOG[target]


def render_profile_yaml(value: HarnessTarget | str) -> str:
    """Render the bundled default profile for one target as YAML."""

    profile = get_target(value).default_profile
    return yaml.safe_dump(profile.model_dump(mode="json", exclude_none=True), sort_keys=False)


def render_target_description(value: HarnessTarget | str) -> str:
    """Render a human-readable target summary for the CLI."""

    entry = get_target(value)
    profile = entry.default_profile
    lines = [
        f"{entry.title} ({entry.target.value})",
        entry.summary,
        "",
        "Surfaces:",
    ]
    for surface in profile.surfaces:
        lines.append(
            "- "
            f"{surface.name}: {surface.path} "
            f"[{surface.ownership_mode.value} / {surface.portability.value}]"
        )
    if profile.flags:
        lines.append("")
        lines.append("Flags:")
        for flag in profile.flags:
            default = flag.default if flag.default is not None else "<none>"
            lines.append(f"- {flag.name}: default={default!r} ({flag.type.value})")
    if profile.hooks:
        lines.append("")
        lines.append("Hooks:")
        for hook in profile.hooks:
            lines.append(f"- {hook.name}: {hook.phase.value} via {hook.runtime.value}")
    if profile.wrappers:
        lines.append("")
        lines.append("Wrappers:")
        for wrapper in profile.wrappers:
            command = " ".join(wrapper.command) if wrapper.command else "<none>"
            lines.append(f"- {wrapper.name}: {command}")
    return "\n".join(lines)
