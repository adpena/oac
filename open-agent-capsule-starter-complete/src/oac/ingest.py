from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from string import Formatter
from typing import Any

from oac.adapters.base import (
    IngestCandidate,
    IngestReport,
    IngestStats,
    IngestSupport,
    LossinessKind,
    OwnershipMode,
    PortabilityClass,
)
from oac.capsule import first_sentence, parse_markdown_record


class ParserKind(str, Enum):
    MARKDOWN = "markdown"
    MANAGED_SECTION = "managed-section"
    JSON = "json"


@dataclass(slots=True)
class IngestRule:
    """Declarative scan rule for one target-native surface."""

    name: str
    patterns: tuple[str, ...]
    kind: str
    surface_name: str
    candidate_path_template: str
    parser: ParserKind = ParserKind.MARKDOWN
    portability: PortabilityClass = PortabilityClass.PORTABLE
    ownership_mode: OwnershipMode = OwnershipMode.MANAGED_FILE
    lossiness: LossinessKind = LossinessKind.PARTIALLY_LOSSLESS
    suggested_canonical_kind: str | None = None
    managed_section_tag: str | None = None
    exclude_names: tuple[str, ...] = ()
    notes: str = ""


@dataclass(slots=True)
class IngestPlan:
    """Target-local ingest contract used by adapters and CLI descriptions."""

    target: str
    support: IngestSupport
    summary: str
    rules: list[IngestRule] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def run_ingest_plan(source_root: Path, plan: IngestPlan) -> IngestReport:
    """Execute a deterministic file-based ingest plan."""

    report = IngestReport(
        target=plan.target,
        source_root=source_root.name or ".",
        support=plan.support,
        notes=list(plan.notes),
    )

    if plan.support != IngestSupport.PARTIAL:
        return report

    scanned_paths: list[Path] = []
    matched_paths: list[Path] = []
    ordered_candidates: list[IngestCandidate] = []
    seen_candidate_ids: set[str] = set()

    for rule in plan.rules:
        for path in _expand_patterns(source_root, rule.patterns):
            scanned_paths.append(path)
            if path.name in rule.exclude_names or not path.is_file():
                continue
            matched_paths.append(path)
            for candidate in _parse_candidate(path, source_root, rule):
                if candidate.candidate_id in seen_candidate_ids:
                    continue
                seen_candidate_ids.add(candidate.candidate_id)
                ordered_candidates.append(candidate)

    report.candidates = ordered_candidates
    report.stats = IngestStats(
        scanned_paths=len({path.relative_to(source_root).as_posix() for path in scanned_paths}),
        matched_paths=len({path.relative_to(source_root).as_posix() for path in matched_paths}),
        candidate_count=len(report.candidates),
        ignored_paths=max(
            len({path.relative_to(source_root).as_posix() for path in scanned_paths})
            - len({path.relative_to(source_root).as_posix() for path in matched_paths}),
            0,
        ),
    )
    return report


def render_ingest_plan(plan: IngestPlan) -> str:
    lines = [
        f"{plan.target} ingest ({plan.support.value})",
        plan.summary,
    ]
    if plan.rules:
        lines.extend(["", "Rules:"])
        for rule in plan.rules:
            patterns = ", ".join(rule.patterns)
            suggested = rule.suggested_canonical_kind or "<review-required>"
            lines.append(
                f"- {rule.name}: {patterns} -> {rule.kind} [{rule.parser.value}] -> {suggested}"
            )
    if plan.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in plan.notes)
    return "\n".join(lines)


def ingest_report_to_dict(report: IngestReport) -> dict[str, Any]:
    return {
        "target": report.target,
        "source_root": report.source_root,
        "support": report.support.value,
        "stats": {
            "scanned_paths": report.stats.scanned_paths,
            "matched_paths": report.stats.matched_paths,
            "candidate_count": report.stats.candidate_count,
            "ignored_paths": report.stats.ignored_paths,
        },
        "notes": report.notes,
        "candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "kind": candidate.kind,
                "suggested_canonical_kind": candidate.suggested_canonical_kind,
                "surface_name": candidate.surface_name,
                "source_path": candidate.source_path,
                "candidate_path_hint": candidate.candidate_path_hint,
                "summary": candidate.summary,
                "portability": candidate.portability.value,
                "ownership_mode": candidate.ownership_mode.value,
                "lossiness": candidate.lossiness.value,
                "metadata": candidate.metadata,
                "content": candidate.content,
            }
            for candidate in report.candidates
        ],
    }


def _expand_patterns(source_root: Path, patterns: tuple[str, ...]) -> list[Path]:
    expanded: list[Path] = []
    for pattern in patterns:
        expanded.extend(sorted(source_root.glob(pattern)))
    return expanded


def _parse_candidate(path: Path, source_root: Path, rule: IngestRule) -> list[IngestCandidate]:
    if rule.parser == ParserKind.MANAGED_SECTION:
        content = _extract_managed_section(
            path.read_text(encoding="utf-8"), rule.managed_section_tag
        )
        if not content.strip():
            return []
        metadata = {"parser": rule.parser.value}
        summary = _markdown_summary_from_text(content, path)
    elif rule.parser == ParserKind.JSON:
        content, metadata = _normalized_json_content(path)
        summary = _json_summary(path, metadata)
    else:
        content = path.read_text(encoding="utf-8").strip() + "\n"
        metadata = _markdown_metadata(path)
        summary = _markdown_summary(path, content)

    relative_path = path.relative_to(source_root).as_posix()
    vars = _path_vars(path, source_root)
    candidate_path_hint = _format_template(rule.candidate_path_template, vars)
    fingerprint = _candidate_fingerprint(rule.kind, relative_path, content)

    metadata.update(
        {
            "rule": rule.name,
            "relative_path": relative_path,
            "surface_name": rule.surface_name,
        }
    )
    if rule.notes:
        metadata["notes"] = rule.notes
    if rule.managed_section_tag:
        metadata["managed_section_tag"] = rule.managed_section_tag

    return [
        IngestCandidate(
            candidate_id=fingerprint,
            kind=rule.kind,
            suggested_canonical_kind=rule.suggested_canonical_kind,
            source_path=relative_path,
            summary=summary,
            portability=rule.portability,
            ownership_mode=rule.ownership_mode,
            lossiness=rule.lossiness,
            surface_name=rule.surface_name,
            content=content,
            candidate_path_hint=candidate_path_hint,
            metadata=metadata,
        )
    ]


def _candidate_fingerprint(kind: str, relative_path: str, content: str) -> str:
    payload = f"{kind}\n{relative_path}\n{content.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _normalized_json_content(path: Path) -> tuple[str, dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip() + "\n", {"parser": ParserKind.JSON.value, "parsed": False}
    content = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    metadata = {
        "parser": ParserKind.JSON.value,
        "parsed": True,
        "top_level_keys": list(payload.keys()) if isinstance(payload, dict) else [],
    }
    return content, metadata


def _json_summary(path: Path, metadata: dict[str, Any]) -> str:
    keys = metadata.get("top_level_keys") or []
    if keys:
        preview = ", ".join(keys[:3])
        return f"{path.name}: {preview}"
    return path.name


def _markdown_metadata(path: Path) -> dict[str, Any]:
    record = parse_markdown_record(path)
    metadata: dict[str, Any] = {"parser": ParserKind.MARKDOWN.value}
    if record.title:
        metadata["title"] = record.title
    if record.summary:
        metadata["declared_summary"] = record.summary
    if record.metadata:
        metadata["frontmatter"] = record.metadata
    return metadata


def _markdown_summary(path: Path, text: str) -> str:
    record = parse_markdown_record(path)
    if record.summary:
        return record.summary
    if record.title:
        return record.title
    return _markdown_summary_from_text(text, path)


def _markdown_summary_from_text(text: str, path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    sentence = first_sentence(text)
    return sentence or path.stem


def _extract_managed_section(text: str, tag: str | None) -> str:
    if tag:
        begin = f"<!-- BEGIN OAC GENERATED:{tag} -->"
        end = f"<!-- END OAC GENERATED:{tag} -->"
        start_index = text.find(begin)
        end_index = text.find(end)
        if start_index != -1 and end_index != -1 and end_index > start_index:
            body = text[start_index + len(begin) : end_index]
            return body.strip() + "\n"
    marker = "<!-- BEGIN OAC GENERATED"
    if marker in text and "<!-- END OAC GENERATED" in text:
        lines: list[str] = []
        capture = False
        for line in text.splitlines():
            if line.startswith("<!-- BEGIN OAC GENERATED"):
                capture = True
                continue
            if line.startswith("<!-- END OAC GENERATED"):
                capture = False
                continue
            if capture:
                lines.append(line)
        if lines:
            return "\n".join(lines).strip() + "\n"
    return text.strip() + "\n"


def _path_vars(path: Path, source_root: Path) -> dict[str, str]:
    relative_path = path.relative_to(source_root).as_posix()
    stem = path.stem
    parent_name = path.parent.name
    return {
        "relative_path": relative_path,
        "file_name": path.name,
        "stem": stem,
        "parent_name": parent_name,
        "skill_name": parent_name if path.name == "SKILL.md" else stem,
        "agent_name": stem,
        "command_name": stem,
        "topic": stem,
        "plugin_name": stem,
    }


def _format_template(template: str, values: dict[str, str]) -> str:
    fields = Formatter().parse(template)
    prepared = {
        field_name: values.get(field_name, "") for _, field_name, _, _ in fields if field_name
    }
    return template.format(**prepared)
