from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oac.capsule import load_capsule


@dataclass(slots=True)
class LexicalIndex:
    """Consolidated keyword-to-record index for a capsule."""

    capsule_id: str
    keywords: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StructuralIndex:
    """High-level index of record kinds and tags."""

    capsule_id: str
    kinds: dict[str, list[str]] = field(default_factory=dict)
    tags: dict[str, list[str]] = field(default_factory=dict)
    record_ids: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def generate_structural_index(capsule_root: Path) -> StructuralIndex:
    """Generate a structural index of kinds and tags."""
    capsule = load_capsule(capsule_root)
    index = StructuralIndex(capsule_id=capsule.manifest.capsule_id)

    def process_record(path: Path, kind: str, record_id: str, metadata: dict[str, Any]):
        relative_path = path.relative_to(capsule_root).as_posix()
        index.kinds.setdefault(kind, []).append(relative_path)
        index.record_ids[relative_path] = record_id
        tags = metadata.get("tags")
        if isinstance(tags, list):
            for tag in tags:
                index.tags.setdefault(str(tag), []).append(relative_path)
        elif isinstance(tags, str):
            for tag in tags.split(","):
                index.tags.setdefault(tag.strip(), []).append(relative_path)

    for group in (capsule.identity, capsule.memory, capsule.procedures):
        for record in group:
            process_record(record.path, record.kind, record.record_id, record.metadata)

    for skill in capsule.skills:
        # Generate a stable ID for skills if not already present (skills are special records)
        skill_id = hashlib.sha256(f"skill:{skill.name}".encode()).hexdigest()[:12]
        process_record(skill.path, "procedure.workflow", skill_id, {"name": skill.name})

    index.notes.append("Structural index generated from record metadata.")
    return index


def write_structural_index(index: StructuralIndex, output_path: Path) -> None:
    """Write the structural index to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "capsule_id": index.capsule_id,
        "kinds": {k: sorted(v) for k, v in sorted(index.kinds.items())},
        "tags": {k: sorted(v) for k, v in sorted(index.tags.items())},
        "record_ids": {k: v for k, v in sorted(index.record_ids.items())},
        "notes": index.notes,
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_lexical_index(capsule_root: Path) -> LexicalIndex:
    """Generate a lexical keyword index from all capsule records."""
    capsule = load_capsule(capsule_root)
    index = LexicalIndex(capsule_id=capsule.manifest.capsule_id)

    # Simple keyword extraction (words > 3 chars, alphanumeric)
    word_pattern = re.compile(r"\b\w{4,}\b")

    def process_record(path: Path, text: str):
        relative_path = path.relative_to(capsule_root).as_posix()
        words = set(word_pattern.findall(text.lower()))
        for word in words:
            index.keywords.setdefault(word, []).append(relative_path)

    for group in (capsule.identity, capsule.memory, capsule.procedures):
        for record in group:
            process_record(record.path, record.body)

    for skill in capsule.skills:
        process_record(skill.path, skill.content)

    index.notes.append("Lexical index generated using basic keyword extraction.")
    return index


def write_lexical_index(index: LexicalIndex, output_path: Path) -> None:
    """Write the lexical index to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "capsule_id": index.capsule_id,
        "keywords": {k: sorted(v) for k, v in sorted(index.keywords.items())},
        "notes": index.notes,
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
