from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from oac.io import load_manifest
from oac.models import CapsuleManifest


@dataclass(slots=True)
class MarkdownRecord:
    path: Path
    kind: str
    record_id: str
    title: str | None
    summary: str | None
    body: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class SkillRecord:
    name: str
    path: Path
    content: str


@dataclass(slots=True)
class Capsule:
    root: Path
    manifest: CapsuleManifest
    identity: list[MarkdownRecord]
    memory: list[MarkdownRecord]
    procedures: list[MarkdownRecord]
    skills: list[SkillRecord]

    def record_by_kind(self, kind: str) -> MarkdownRecord | None:
        for group in (self.identity, self.memory, self.procedures):
            for record in group:
                if record.kind == kind:
                    return record
        return None

    @property
    def display_identity(self) -> MarkdownRecord | None:
        return self.record_by_kind("identity.display")

    @property
    def persona(self) -> MarkdownRecord | None:
        return self.record_by_kind("identity.persona")

    @property
    def user_model(self) -> MarkdownRecord | None:
        return self.record_by_kind("user.model")

    @property
    def semantic_memory(self) -> list[MarkdownRecord]:
        return [record for record in self.memory if record.kind == "memory.semantic"]

    def semantic_bullets(self) -> list[str]:
        bullets: list[str] = []
        for record in self.semantic_memory:
            bullets.extend(markdown_bullets(record.body))
        return bullets


def load_capsule(path: str | Path, record_kinds: list[str] | None = None) -> Capsule:
    root = Path(path)
    manifest = load_manifest(root)
    if root.is_file():
        root = root.parent

    canonical = manifest.canonical_paths
    return Capsule(
        root=root,
        manifest=manifest,
        identity=_load_markdown_tree(root / canonical.identity, record_kinds),
        memory=_load_markdown_tree(root / canonical.memory, record_kinds),
        procedures=_load_markdown_tree(root / canonical.procedures, record_kinds),
        skills=_load_skills(root / canonical.skills, record_kinds),
    )


def _load_markdown_tree(root: Path, record_kinds: list[str] | None = None) -> list[MarkdownRecord]:
    if not root.exists():
        return []
    records: list[MarkdownRecord] = []
    for path in sorted(root.rglob("*.md")):
        record = parse_markdown_record(path)
        if record_kinds is None or record.kind in record_kinds:
            records.append(record)
    return records


def _load_skills(root: Path, record_kinds: list[str] | None = None) -> list[SkillRecord]:
    if not root.exists():
        return []
    if record_kinds is not None and "procedure.workflow" not in record_kinds:
        return []
    skills: list[SkillRecord] = []
    for path in sorted(root.rglob("SKILL.md")):
        name = path.parent.name
        skills.append(SkillRecord(name=name, path=path, content=path.read_text(encoding="utf-8")))
    return skills


def parse_markdown_record(path: str | Path) -> MarkdownRecord:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    body = text.strip()

    if text.startswith("---\n"):
        marker = "\n---\n"
        end = text.find(marker, 4)
        if end != -1:
            frontmatter_text = text[4:end]
            metadata = yaml.safe_load(frontmatter_text) or {}
            if not isinstance(metadata, dict):
                raise TypeError(f"Frontmatter must be a mapping in {file_path}")
            body = text[end + len(marker) :].strip()

    kind = str(metadata.get("kind", "document"))
    title = _maybe_str(metadata.get("title"))
    summary = _maybe_str(metadata.get("summary")) or _maybe_str(metadata.get("name"))

    record_id = _maybe_str(metadata.get("id"))
    if not record_id:
        # Generate a deterministic ID based on the initial path + kind
        payload = f"{kind}:{file_path.name}"
        record_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]

    return MarkdownRecord(
        path=file_path,
        kind=kind,
        record_id=record_id,
        title=title,
        summary=summary,
        body=body,
        metadata=metadata,
    )


def markdown_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def first_sentence(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _maybe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
