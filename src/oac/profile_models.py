from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from oac.adapters.base import OwnershipMode, PortabilityClass
from oac.models import HarnessTarget

ScalarValue = str | int | bool
DefaultValue = ScalarValue | list[str] | None


class FlagType(str, Enum):
    """High-level shape of a profile flag value."""

    BOOL = "bool"
    STRING = "string"
    INTEGER = "integer"
    STRING_LIST = "string-list"
    PATH = "path"
    ENUM = "enum"


class MappingMode(str, Enum):
    """How a canonical record should materialize at a target surface."""

    MANAGED_SECTION = "managed-section"
    MANAGED_FILE = "managed-file"
    IMPORTED_FILE = "imported-file"
    INDEX_FILE = "index-file"
    TOPIC_FILES = "topic-files"
    SIDECAR = "sidecar"
    RESOURCE = "resource"


class HookPhase(str, Enum):
    """Lifecycle phases where advanced users may attach custom logic."""

    PRE_HYDRATE = "pre-hydrate"
    POST_HYDRATE = "post-hydrate"
    PRE_INGEST = "pre-ingest"
    POST_INGEST = "post-ingest"
    PRE_PROMOTE = "pre-promote"
    POST_PROMOTE = "post-promote"


class HookRuntime(str, Enum):
    """Supported hook implementation runtimes for starter examples."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    SHELL = "shell"
    ZIG = "zig"
    GO = "go"
    RUST = "rust"
    WASM = "wasm"


class SurfaceSpec(BaseModel):
    """One target-native surface exposed by an adapter profile."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    ownership_mode: OwnershipMode
    portability: PortabilityClass = PortabilityClass.PORTABLE
    notes: str = ""


class FlagSpec(BaseModel):
    """A canonical adapter flag with an optional harness-local alias."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    cli_name: str | None = None
    harness_name: str | None = None
    type: FlagType = FlagType.STRING
    default: DefaultValue = None
    description: str = ""
    example: str | None = None


class MappingRule(BaseModel):
    """A declarative mapping from canonical record kind to target surface."""

    model_config = ConfigDict(extra="forbid")

    canonical_kind: str = Field(min_length=1)
    target_surface: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    mode: MappingMode
    ownership_mode: OwnershipMode
    portability: PortabilityClass = PortabilityClass.PORTABLE
    notes: str = ""


class HookSpec(BaseModel):
    """One opt-in hook that may run around hydrate or ingest steps."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    phase: HookPhase
    runtime: HookRuntime = HookRuntime.PYTHON
    entrypoint: str = Field(min_length=1)
    enabled: bool = False
    timeout_seconds: int = Field(default=30, ge=1, le=600)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class WrapperSpec(BaseModel):
    """A named launcher wrapper for a harness installation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    command: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class AdapterProfile(BaseModel):
    """Schema-backed adapter customization layer.

    The default profile shipped by OAC gives every harness a canonical set of surfaces,
    flags, mappings, hooks, and wrappers. Users can copy that profile and adapt paths,
    naming conventions, and opt-in hook behavior to match their actual environment.
    """

    model_config = ConfigDict(extra="forbid")

    format: str = Field(default="oac.adapter-profile.v0")
    profile_name: str = Field(min_length=1)
    target: HarnessTarget
    description: str = ""
    surfaces: list[SurfaceSpec] = Field(default_factory=list)
    flags: list[FlagSpec] = Field(default_factory=list)
    mappings: list[MappingRule] = Field(default_factory=list)
    hooks: list[HookSpec] = Field(default_factory=list)
    wrappers: list[WrapperSpec] = Field(default_factory=list)
