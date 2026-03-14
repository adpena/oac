from __future__ import annotations

import difflib
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from oac.adapters.base import IngestCandidate, IngestReport, PortabilityClass
from oac.capsule import Capsule, load_capsule
from oac.io import write_text


class ProposalDisposition(str, Enum):
    """How a candidate should move through review."""

    PROMOTABLE = "promotable"
    NOOP = "noop"
    DEFERRED = "deferred"
    TARGET_LOCAL = "target-local"
    USER_LOCAL = "user-local"
    RUNTIME_STATE = "runtime-state"
    UNSUPPORTED = "unsupported"


class PromotionOperation(str, Enum):
    """Planned file-system mutation for a promotable record."""

    CREATE = "create"
    UPDATE = "update"
    SKIP = "skip"


@dataclass(slots=True)
class ProposalRecord:
    """One reviewable proposal derived from an ingest candidate."""

    proposal_id: str
    candidate_id: str
    target: str
    disposition: ProposalDisposition
    operation: PromotionOperation
    kind: str
    canonical_kind: str | None
    source_path: str
    surface_name: str
    summary: str
    candidate_path_hint: str
    canonical_path: str | None
    rationale: str
    content: str
    canonical_content: str
    current_content: str
    diff: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProposalStats:
    """Deterministic proposal counters."""

    total: int = 0
    promotable: int = 0
    noop: int = 0
    deferred: int = 0
    target_local: int = 0
    user_local: int = 0
    runtime_state: int = 0
    unsupported: int = 0


@dataclass(slots=True)
class ProposalBundle:
    """All proposal records derived from one ingest run."""

    target: str
    capsule_id: str
    source_root: str
    records: list[ProposalRecord] = field(default_factory=list)
    stats: ProposalStats = field(default_factory=ProposalStats)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PromotionChange:
    """One promoted file change, with backup metadata for reversal."""

    proposal_id: str
    canonical_path: str
    operation: PromotionOperation
    applied: bool
    backup_path: str | None = None


@dataclass(slots=True)
class PromotionReport:
    """Result of previewing or applying a proposal bundle."""

    promotion_id: str
    capsule_id: str
    proposal_target: str
    applied: bool
    eval_required: bool
    eval_passed: bool
    change_count: int
    changes: list[PromotionChange] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RevertReport:
    """Result of restoring a prior promotion from backups."""

    promotion_id: str
    reverted_count: int
    restored_count: int
    deleted_count: int
    notes: list[str] = field(default_factory=list)


def create_proposal_bundle(capsule_root: Path, ingest_report: IngestReport) -> ProposalBundle:
    """Turn an ingest report into an explicit review bundle."""

    capsule = load_capsule(capsule_root)
    records = [
        _proposal_record_from_candidate(capsule, ingest_report.target, candidate)
        for candidate in ingest_report.candidates
    ]
    bundle = ProposalBundle(
        target=ingest_report.target,
        capsule_id=capsule.manifest.capsule_id,
        source_root=ingest_report.source_root,
        records=records,
        stats=_proposal_stats(records),
        notes=list(ingest_report.notes),
    )
    return bundle


def render_proposal_bundle(bundle: ProposalBundle) -> str:
    lines = [
        f"proposal bundle: {bundle.target}",
        f"capsule: {bundle.capsule_id}",
        f"records: {bundle.stats.total}",
        f"promotable: {bundle.stats.promotable}",
        f"noop: {bundle.stats.noop}",
        f"deferred: {bundle.stats.deferred}",
    ]
    for record in bundle.records:
        destination = record.canonical_path or "<no canonical destination>"
        line = (
            f"- {record.disposition.value}: {record.source_path} -> {destination} "
            f"[{record.operation.value}]"
        )
        lines.append(line)
    return "\n".join(lines)


def proposal_bundle_to_dict(bundle: ProposalBundle) -> dict[str, Any]:
    return {
        "target": bundle.target,
        "capsule_id": bundle.capsule_id,
        "source_root": bundle.source_root,
        "stats": {
            "total": bundle.stats.total,
            "promotable": bundle.stats.promotable,
            "noop": bundle.stats.noop,
            "deferred": bundle.stats.deferred,
            "target_local": bundle.stats.target_local,
            "user_local": bundle.stats.user_local,
            "runtime_state": bundle.stats.runtime_state,
            "unsupported": bundle.stats.unsupported,
        },
        "notes": bundle.notes,
        "records": [
            {
                "proposal_id": record.proposal_id,
                "candidate_id": record.candidate_id,
                "target": record.target,
                "disposition": record.disposition.value,
                "operation": record.operation.value,
                "kind": record.kind,
                "canonical_kind": record.canonical_kind,
                "source_path": record.source_path,
                "surface_name": record.surface_name,
                "summary": record.summary,
                "candidate_path_hint": record.candidate_path_hint,
                "canonical_path": record.canonical_path,
                "rationale": record.rationale,
                "metadata": record.metadata,
                "content": record.content,
                "canonical_content": record.canonical_content,
                "current_content": record.current_content,
                "diff": record.diff,
            }
            for record in bundle.records
        ],
    }


def write_proposal_bundle(bundle: ProposalBundle, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(proposal_bundle_to_dict(bundle), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return target


def load_proposal_bundle(path: str | Path) -> ProposalBundle:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    stats_payload = payload.get("stats", {})
    records = [
        ProposalRecord(
            proposal_id=str(item["proposal_id"]),
            candidate_id=str(item["candidate_id"]),
            target=str(item["target"]),
            disposition=ProposalDisposition(item["disposition"]),
            operation=PromotionOperation(item["operation"]),
            kind=str(item["kind"]),
            canonical_kind=item.get("canonical_kind"),
            source_path=str(item["source_path"]),
            surface_name=str(item["surface_name"]),
            summary=str(item["summary"]),
            candidate_path_hint=str(item["candidate_path_hint"]),
            canonical_path=item.get("canonical_path"),
            rationale=str(item["rationale"]),
            content=str(item.get("content", "")),
            canonical_content=str(item.get("canonical_content", "")),
            current_content=str(item.get("current_content", "")),
            diff=str(item.get("diff", "")),
            metadata=dict(item.get("metadata", {})),
        )
        for item in payload.get("records", [])
    ]
    return ProposalBundle(
        target=str(payload["target"]),
        capsule_id=str(payload["capsule_id"]),
        source_root=str(payload["source_root"]),
        records=records,
        stats=ProposalStats(
            total=int(stats_payload.get("total", len(records))),
            promotable=int(stats_payload.get("promotable", 0)),
            noop=int(stats_payload.get("noop", 0)),
            deferred=int(stats_payload.get("deferred", 0)),
            target_local=int(stats_payload.get("target_local", 0)),
            user_local=int(stats_payload.get("user_local", 0)),
            runtime_state=int(stats_payload.get("runtime_state", 0)),
            unsupported=int(stats_payload.get("unsupported", 0)),
        ),
        notes=[str(note) for note in payload.get("notes", [])],
    )


def preview_promotion(
    bundle: ProposalBundle,
    capsule_root: Path,
    *,
    apply: bool,
    eval_passed: bool,
    output_root: Path | None = None,
) -> PromotionReport:
    """Apply or preview promotable files from a bundle.

    When ``apply`` is true, writes canonical files and stores backups under a stable promotion
    directory. When false, the function stays read-only unless ``output_root`` is provided.
    """

    promotion_id = _promotion_id(bundle)
    promotion_root = output_root or (capsule_root / ".oac" / "promotions" / promotion_id)
    backup_root = promotion_root / "backups"
    proposal_path = promotion_root / "proposal.json"
    changes: list[PromotionChange] = []

    for record in bundle.records:
        if record.disposition != ProposalDisposition.PROMOTABLE or not record.canonical_path:
            continue
        destination = capsule_root / record.canonical_path
        backup_path: str | None = None
        if record.operation != PromotionOperation.SKIP and apply:
            if destination.exists():
                backup_target = backup_root / record.canonical_path
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup_target)
                backup_path = str(backup_target.relative_to(promotion_root))
            write_text(destination, record.canonical_content)
        changes.append(
            PromotionChange(
                proposal_id=record.proposal_id,
                canonical_path=record.canonical_path,
                operation=record.operation,
                applied=apply and record.operation != PromotionOperation.SKIP,
                backup_path=backup_path,
            )
        )

    report = PromotionReport(
        promotion_id=promotion_id,
        capsule_id=bundle.capsule_id,
        proposal_target=bundle.target,
        applied=apply,
        eval_required=True,
        eval_passed=eval_passed,
        change_count=len(changes),
        changes=changes,
        notes=[
            "Promotions only apply records marked promotable.",
            "Backups are stored for every updated file when apply=true.",
        ],
    )

    if apply or output_root is not None:
        promotion_root.mkdir(parents=True, exist_ok=True)
        write_proposal_bundle(bundle, proposal_path)
        (promotion_root / "promotion.json").write_text(
            json.dumps(promotion_report_to_dict(report), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )

    return report


def revert_promotion(
    promotion_report_path: str | Path, capsule_root: Path, *, apply: bool
) -> RevertReport:
    """Restore backups captured during a prior promotion."""

    report_path = Path(promotion_report_path)
    promotion_root = report_path.parent
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    restored_count = 0
    deleted_count = 0

    for change in payload.get("changes", []):
        if not change.get("applied"):
            continue
        canonical_path = str(change["canonical_path"])
        destination = capsule_root / canonical_path
        backup_path = change.get("backup_path")
        if backup_path:
            backup = promotion_root / backup_path
            if apply:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, destination)
            restored_count += 1
            continue
        if change.get("operation") == PromotionOperation.CREATE.value:
            if apply and destination.exists():
                destination.unlink()
            deleted_count += 1

    return RevertReport(
        promotion_id=str(payload["promotion_id"]),
        reverted_count=restored_count + deleted_count,
        restored_count=restored_count,
        deleted_count=deleted_count,
        notes=["Revert uses stored backups when available and deletes created files otherwise."],
    )


def promotion_report_to_dict(report: PromotionReport) -> dict[str, Any]:
    return {
        "promotion_id": report.promotion_id,
        "capsule_id": report.capsule_id,
        "proposal_target": report.proposal_target,
        "applied": report.applied,
        "eval_required": report.eval_required,
        "eval_passed": report.eval_passed,
        "change_count": report.change_count,
        "notes": report.notes,
        "changes": [
            {
                "proposal_id": change.proposal_id,
                "canonical_path": change.canonical_path,
                "operation": change.operation.value,
                "applied": change.applied,
                "backup_path": change.backup_path,
            }
            for change in report.changes
        ],
    }


def revert_report_to_dict(report: RevertReport) -> dict[str, Any]:
    return {
        "promotion_id": report.promotion_id,
        "reverted_count": report.reverted_count,
        "restored_count": report.restored_count,
        "deleted_count": report.deleted_count,
        "notes": report.notes,
    }


def materialize_bundle(bundle: ProposalBundle, destination_root: Path) -> None:
    """Write promotable records into a staged capsule copy without backups."""

    for record in bundle.records:
        if record.disposition != ProposalDisposition.PROMOTABLE or not record.canonical_path:
            continue
        if record.operation == PromotionOperation.SKIP:
            continue
        write_text(destination_root / record.canonical_path, record.canonical_content)


def _proposal_record_from_candidate(
    capsule: Capsule,
    target: str,
    candidate: IngestCandidate,
) -> ProposalRecord:
    canonical_kind = candidate.suggested_canonical_kind or candidate.kind
    disposition, canonical_path, rationale = _resolve_destination(
        capsule, target, candidate, canonical_kind
    )
    canonical_content = ""
    current_content = ""
    operation = PromotionOperation.SKIP

    if disposition in {ProposalDisposition.PROMOTABLE, ProposalDisposition.NOOP} and canonical_path:
        canonical_content = _render_canonical_content(
            candidate, target, canonical_kind, canonical_path
        )
        destination = capsule.root / canonical_path
        if destination.exists():
            current_content = destination.read_text(encoding="utf-8")
        if current_content == canonical_content:
            disposition = ProposalDisposition.NOOP
            operation = PromotionOperation.SKIP
        else:
            disposition = ProposalDisposition.PROMOTABLE
            operation = (
                PromotionOperation.UPDATE if destination.exists() else PromotionOperation.CREATE
            )

    diff = _unified_diff(current_content, canonical_content, canonical_path)
    proposal_id = _proposal_id(
        target, candidate.candidate_id, canonical_kind, canonical_path, canonical_content
    )

    return ProposalRecord(
        proposal_id=proposal_id,
        candidate_id=candidate.candidate_id,
        target=target,
        disposition=disposition,
        operation=operation,
        kind=candidate.kind,
        canonical_kind=canonical_kind if canonical_path else None,
        source_path=candidate.source_path,
        surface_name=candidate.surface_name,
        summary=candidate.summary,
        candidate_path_hint=candidate.candidate_path_hint,
        canonical_path=canonical_path,
        rationale=rationale,
        content=_normalize_text(candidate.content),
        canonical_content=canonical_content,
        current_content=current_content,
        diff=diff,
        metadata={
            **candidate.metadata,
            "portability": candidate.portability.value,
            "ownership_mode": candidate.ownership_mode.value,
            "lossiness": candidate.lossiness.value,
        },
    )


def _resolve_destination(
    capsule: Capsule,
    target: str,
    candidate: IngestCandidate,
    canonical_kind: str,
) -> tuple[ProposalDisposition, str | None, str]:
    canonical = capsule.manifest.canonical_paths
    if candidate.portability == PortabilityClass.USER_LOCAL:
        return (
            ProposalDisposition.USER_LOCAL,
            None,
            "User-local material is not promoted by default.",
        )
    if candidate.portability == PortabilityClass.RUNTIME_STATE:
        return (
            ProposalDisposition.RUNTIME_STATE,
            None,
            "Runtime state never promotes automatically.",
        )
    if canonical_kind == "config.signal":
        return (
            ProposalDisposition.DEFERRED,
            None,
            "Config signals need manual abstraction before promotion.",
        )
    if canonical_kind == "hook.logic":
        return (
            ProposalDisposition.DEFERRED,
            None,
            "Hook logic stays deferred until the canonical hook store lands.",
        )

    if canonical_kind == "identity.display":
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.identity}/identity.md",
            "Identity display can overwrite the shared display identity.",
        )
    if canonical_kind == "identity.persona":
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.identity}/persona.md",
            "Persona updates map into the canonical identity tree.",
        )
    if canonical_kind == "user.model":
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.identity}/user-model.md",
            "User-model updates belong in the identity tree.",
        )
    if canonical_kind.startswith("memory."):
        slug = _slug(_summary_or_name(candidate))
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.memory}/semantic/{slug}.memory.md",
            "Portable semantic memory promotes into canonical memory/semantic/.",
        )
    if canonical_kind == "procedure.workflow":
        if candidate.source_path.endswith("SKILL.md") or "skill" in candidate.surface_name:
            skill_name = Path(candidate.source_path).parent.name or _slug(
                _summary_or_name(candidate)
            )
            return (
                ProposalDisposition.PROMOTABLE,
                f"{canonical.skills}/{skill_name}/SKILL.md",
                "Skill-like workflows promote into canonical skills/.",
            )
        slug = _slug(_summary_or_name(candidate))
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.procedures}/workflows/{slug}.md",
            "Non-skill workflows promote into canonical procedures/workflows/.",
        )
    if canonical_kind == "behavior.rule":
        slug = _slug(_summary_or_name(candidate))
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.procedures}/behavior/{target}-{slug}.md",
            "Portable rules promote into canonical procedures/behavior/.",
        )
    if canonical_kind == "agent.specialist":
        slug = _slug(_summary_or_name(candidate))
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.procedures}/agents/{slug}.md",
            "Specialist agent prompts promote into canonical procedures/agents/.",
        )
    if canonical_kind == "command.template":
        slug = _slug(_summary_or_name(candidate))
        return (
            ProposalDisposition.PROMOTABLE,
            f"{canonical.procedures}/commands/{slug}.md",
            "Command templates promote into canonical procedures/commands/.",
        )
    return (
        ProposalDisposition.UNSUPPORTED,
        None,
        "No canonical destination is defined for this candidate kind yet.",
    )


def _render_canonical_content(
    candidate: IngestCandidate,
    target: str,
    canonical_kind: str,
    canonical_path: str,
) -> str:
    if canonical_path.endswith("/SKILL.md") or canonical_path.endswith("SKILL.md"):
        return _normalize_text(candidate.content)

    body = _markdown_body(candidate.content)
    summary = _summary_or_name(candidate)
    payload = {
        "kind": canonical_kind,
        "summary": summary,
        "source_target": target,
        "source_surface": candidate.surface_name,
    }
    frontmatter = yaml.safe_dump(payload, sort_keys=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def _markdown_body(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("---\n"):
        marker = "\n---\n"
        end = stripped.find(marker, 4)
        if end != -1:
            body = stripped[end + len(marker) :].strip()
            return body
    return stripped


def _summary_or_name(candidate: IngestCandidate) -> str:
    frontmatter = candidate.metadata.get("frontmatter")
    if isinstance(frontmatter, dict):
        for key in ("title", "name", "summary"):
            value = frontmatter.get(key)
            if value:
                return str(value)
    return candidate.summary or Path(candidate.source_path).stem


def _unified_diff(current_content: str, canonical_content: str, canonical_path: str | None) -> str:
    destination = canonical_path or "<none>"
    if not canonical_content and not current_content:
        return ""
    diff = difflib.unified_diff(
        current_content.splitlines(keepends=True),
        canonical_content.splitlines(keepends=True),
        fromfile=f"current:{destination}",
        tofile=f"proposed:{destination}",
    )
    return "".join(diff)


def _proposal_stats(records: list[ProposalRecord]) -> ProposalStats:
    stats = ProposalStats(total=len(records))
    for record in records:
        if record.disposition == ProposalDisposition.PROMOTABLE:
            stats.promotable += 1
        elif record.disposition == ProposalDisposition.NOOP:
            stats.noop += 1
        elif record.disposition == ProposalDisposition.DEFERRED:
            stats.deferred += 1
        elif record.disposition == ProposalDisposition.TARGET_LOCAL:
            stats.target_local += 1
        elif record.disposition == ProposalDisposition.USER_LOCAL:
            stats.user_local += 1
        elif record.disposition == ProposalDisposition.RUNTIME_STATE:
            stats.runtime_state += 1
        elif record.disposition == ProposalDisposition.UNSUPPORTED:
            stats.unsupported += 1
    return stats


def _proposal_id(
    target: str,
    candidate_id: str,
    canonical_kind: str,
    canonical_path: str | None,
    canonical_content: str,
) -> str:
    payload = "\n".join(
        [target, candidate_id, canonical_kind, canonical_path or "", canonical_content]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _promotion_id(bundle: ProposalBundle) -> str:
    payload = bundle.capsule_id + "\n" + "\n".join(record.proposal_id for record in bundle.records)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _slug(value: str) -> str:
    cleaned = []
    previous_dash = False
    for character in value.lower():
        if character.isalnum():
            cleaned.append(character)
            previous_dash = False
            continue
        if not previous_dash:
            cleaned.append("-")
            previous_dash = True
    slug = "".join(cleaned).strip("-")
    return slug or "record"


def _normalize_text(text: str) -> str:
    return text.strip() + "\n"
