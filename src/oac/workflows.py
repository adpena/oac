from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class WorkflowStatus(str, Enum):
    """Lifecycle state of a promotion workflow."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PROMOTED = "promoted"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class PromotionWorkflow:
    """Durable state for a long-running promotion flow."""

    workflow_id: str
    capsule_id: str
    proposal_path: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    history: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def create_promotion_workflow(proposal_path: Path, capsule_id: str) -> PromotionWorkflow:
    """Initialize a new promotion workflow from a proposal."""
    workflow_id = f"wf-{proposal_path.stem}"
    workflow = PromotionWorkflow(
        workflow_id=workflow_id, capsule_id=capsule_id, proposal_path=str(proposal_path)
    )
    workflow.history.append(
        {
            "status": WorkflowStatus.DRAFT.value,
            "timestamp": "2026-03-12T12:00:00Z",  # Placeholder
            "note": "Workflow initialized from proposal bundle.",
        }
    )
    return workflow


def write_workflow(workflow: PromotionWorkflow, output_path: Path) -> None:
    """Write the workflow state to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "workflow_id": workflow.workflow_id,
        "capsule_id": workflow.capsule_id,
        "proposal_path": workflow.proposal_path,
        "status": workflow.status.value,
        "history": workflow.history,
        "notes": workflow.notes,
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_workflow(path: Path) -> PromotionWorkflow:
    """Load a workflow state from a JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PromotionWorkflow(
        workflow_id=payload["workflow_id"],
        capsule_id=payload["capsule_id"],
        proposal_path=payload["proposal_path"],
        status=WorkflowStatus(payload["status"]),
        history=payload.get("history", []),
        notes=payload.get("notes", []),
    )
