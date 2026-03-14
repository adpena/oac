from __future__ import annotations

from oac.adapters.base import (
    AdapterOptions,
    HarnessAdapter,
    IngestCandidate,
    IngestReport,
    IngestStats,
    IngestSupport,
    LossinessKind,
    OwnershipMode,
    PortabilityClass,
    ProjectionArtifact,
    ProjectionReport,
)


def _registry():
    from oac.adapters.claude_code import ClaudeCodeAdapter
    from oac.adapters.codex import CodexAdapter
    from oac.adapters.gemini import GeminiAdapter
    from oac.adapters.mcp import MCPAdapter
    from oac.adapters.openclaw import OpenClawAdapter
    from oac.adapters.opencode import OpenCodeAdapter
    from oac.adapters.webmcp import WebMCPAdapter

    return {
        "codex": CodexAdapter(),
        "openclaw": OpenClawAdapter(),
        "claude-code": ClaudeCodeAdapter(),
        "opencode": OpenCodeAdapter(),
        "gemini": GeminiAdapter(),
        "mcp": MCPAdapter(),
        "webmcp": WebMCPAdapter(),
    }


def get_adapter(target: str):
    registry = _registry()
    try:
        return registry[target]
    except KeyError as exc:
        raise ValueError(f"Unknown target: {target}") from exc


def list_adapters() -> list[str]:
    return list(_registry())


__all__ = [
    "AdapterOptions",
    "HarnessAdapter",
    "IngestCandidate",
    "IngestReport",
    "IngestStats",
    "IngestSupport",
    "LossinessKind",
    "OwnershipMode",
    "PortabilityClass",
    "ProjectionArtifact",
    "ProjectionReport",
    "get_adapter",
    "list_adapters",
]
