from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class HarnessTarget(str, Enum):
    """Known target harnesses for a projection."""

    CODEX = "codex"
    OPENCLAW = "openclaw"
    CLAUDE_CODE = "claude-code"
    OPENCODE = "opencode"
    GEMINI = "gemini"
    MCP = "mcp"
    WEBMCP = "webmcp"


class ProjectionMode(str, Enum):
    """How a target is served or materialized."""

    NATIVE_FILES = "native-files"
    MCP = "mcp"
    SDK = "sdk"
    NONE = "none"


class CanonicalPaths(BaseModel):
    """Directory contracts for canonical source material."""

    model_config = ConfigDict(extra="forbid")

    identity: str = "identity"
    memory: str = "memory"
    procedures: str = "procedures"
    skills: str = "skills"
    provenance: str = "provenance"


class ProjectionTarget(BaseModel):
    """A supported target projection."""

    model_config = ConfigDict(extra="forbid")

    name: HarnessTarget
    mode: ProjectionMode = ProjectionMode.NATIVE_FILES
    enabled: bool = True
    notes: str | None = None


class CapsuleManifest(BaseModel):
    """Minimal manifest for an Open Agent Capsule."""

    model_config = ConfigDict(extra="forbid")

    format: str = Field(default="oac.v0", description="Manifest format identifier.")
    capsule_id: str = Field(min_length=1, description="Stable capsule identifier.")
    name: str = Field(min_length=1, description="Human-readable capsule name.")
    description: str = Field(default="", description="Short description of purpose.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Manifest creation time in UTC.",
    )
    license: str = Field(default="Apache-2.0", description="Project license identifier.")
    owners: list[str] = Field(default_factory=list, description="Primary maintainers.")
    canonical_paths: CanonicalPaths = Field(default_factory=CanonicalPaths)
    targets: list[ProjectionTarget] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Simple validation summary for CLI output and tests."""

    model_config = ConfigDict(extra="forbid")

    manifest_path: str
    capsule_id: str
    target_count: int
    format: str
