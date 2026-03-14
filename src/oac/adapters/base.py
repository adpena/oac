"""Shared adapter contracts for harness projection and ingest work.

The starter treats every harness adapter as a bidirectional compiler:

- ``hydrate`` turns canonical capsule records into native harness files or services.
- ``ingest`` turns harness-local edits back into typed candidate records.
- every pass reports ownership mode, portability class, and lossiness.
- adapter profiles may override paths, flags, hooks, and wrappers without changing the
  canonical capsule format.

The types stay intentionally small and plain so the repo is easy to extend from Python,
Rust, Go, TypeScript, Zig, or WASM-hosted helpers later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

FlagValue = str | int | bool | list[str]


class PortabilityClass(str, Enum):
    """How broadly a record may travel.

    ``PORTABLE`` is safe to share in the canonical capsule.
    ``USER_LOCAL`` is useful, but should stay out of the shared project by default.
    ``RUNTIME_STATE`` covers credentials, provider caches, or machine-owned state.
    """

    PORTABLE = "portable"
    USER_LOCAL = "user-local"
    RUNTIME_STATE = "runtime-state"


class OwnershipMode(str, Enum):
    """Who owns the emitted artifact or section.

    Use ``MANAGED_FILE`` when OAC controls the whole file.
    Use ``MANAGED_SECTION`` when OAC only owns marked regions.
    Use ``IMPORTED_FILE`` when the harness points at an OAC-generated file.
    Use ``SIDECAR`` for non-canonical, nearby runtime data.
    """

    MANAGED_FILE = "managed-file"
    MANAGED_SECTION = "managed-section"
    IMPORTED_FILE = "imported-file"
    SIDECAR = "sidecar"


class LossinessKind(str, Enum):
    """How faithfully a projection can round-trip."""

    LOSSLESS = "lossless"
    PARTIALLY_LOSSLESS = "partially-lossless"
    ONE_WAY_SUMMARY = "one-way-summary"
    UNSUPPORTED = "unsupported"


class IngestSupport(str, Enum):
    """Current maturity of a target ingest path."""

    PARTIAL = "partial"
    READ_ONLY = "read-only"
    UNSUPPORTED = "unsupported"


@dataclass(slots=True)
class AdapterOptions:
    """Cross-adapter execution flags.

    These are deliberately conservative. Real implementations will likely grow more
    target-specific settings, but a shared minimum helps tests, profiles, and examples stay
    aligned.
    """

    dry_run: bool = False
    include_user_local: bool = False
    allow_sidecars: bool = False
    ownership_mode: OwnershipMode | None = None
    generated_by: str = "oac"
    profile_path: str | None = None
    schema_override_path: str | None = None
    enable_hooks: bool = True
    selected_wrapper: str | None = None
    flag_overrides: dict[str, FlagValue] = field(default_factory=dict)
    incremental_state_path: str | None = None
    record_kinds: list[str] | None = None


@dataclass(slots=True)
class ProjectionArtifact:
    """One emitted file or surface description."""

    path: str
    summary: str
    ownership_mode: OwnershipMode


@dataclass(slots=True)
class ProjectionReport:
    """Result of hydrating a capsule into a target harness."""

    target: str
    destination: str
    ownership_mode: OwnershipMode
    lossiness: LossinessKind
    updated_count: int = 0
    unchanged_count: int = 0
    artifacts: list[ProjectionArtifact] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IngestCandidate:
    """A typed candidate extracted from target-native files.

    ``kind`` names the native or candidate-side abstraction discovered during ingest.
    It may be broader than the canonical record kinds, because ingest should be free to
    capture harness-native concepts first and only later decide how they promote.
    """

    candidate_id: str
    kind: str
    source_path: str
    summary: str
    portability: PortabilityClass
    ownership_mode: OwnershipMode
    lossiness: LossinessKind
    surface_name: str
    content: str
    candidate_path_hint: str
    suggested_canonical_kind: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IngestStats:
    """Small deterministic counters for ingest reports."""

    scanned_paths: int = 0
    matched_paths: int = 0
    candidate_count: int = 0
    ignored_paths: int = 0
    unchanged_count: int = 0


@dataclass(slots=True)
class IngestReport:
    """Result of scanning a harness-local projection for durable updates."""

    target: str
    source_root: str
    support: IngestSupport = IngestSupport.PARTIAL
    candidates: list[IngestCandidate] = field(default_factory=list)
    stats: IngestStats = field(default_factory=IngestStats)
    notes: list[str] = field(default_factory=list)


class HarnessAdapter(Protocol):
    """Protocol implemented by every harness adapter.

    Example:
        >>> from pathlib import Path
        >>> from oac.adapters.codex import CodexAdapter
        >>> adapter = CodexAdapter()
        >>> isinstance(adapter.name, str)
        True

    The real implementation path is expected to be:

    1. load canonical records from the capsule
    2. classify them by portability class
    3. choose ownership mode for each emitted artifact
    4. optionally load an adapter profile for path and hook overrides
    5. render native files or resources deterministically
    6. emit a lossiness report for anything externalized or unsupported
    7. scan native surfaces back into typed candidates for proposal/review
    """

    name: str

    def hydrate(
        self,
        capsule_root: Path,
        destination: Path,
        options: AdapterOptions | None = None,
    ) -> ProjectionReport: ...

    def ingest(
        self,
        source_root: Path,
        capsule_root: Path,
        options: AdapterOptions | None = None,
    ) -> IngestReport: ...
