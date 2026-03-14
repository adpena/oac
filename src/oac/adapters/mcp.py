from __future__ import annotations

from pathlib import Path

from oac.adapter_utils import (
    load_effective_profile,
    record_artifact,
    write_json_if_changed,
)
from oac.adapters.base import (
    AdapterOptions,
    IngestReport,
    IngestSupport,
    LossinessKind,
    OwnershipMode,
    ProjectionReport,
)
from oac.capsule import load_capsule
from oac.ingest import IngestPlan, run_ingest_plan


class MCPAdapter:
    """Hydrate a read-only MCP companion surface."""

    name = "mcp"
    default_ownership_mode = OwnershipMode.MANAGED_FILE

    def hydrate(
        self,
        capsule_root: Path,
        destination: Path,
        options: AdapterOptions | None = None,
    ) -> ProjectionReport:
        options = options or AdapterOptions()
        capsule = load_capsule(capsule_root, options.record_kinds)
        profile = load_effective_profile(self.name, options.profile_path)

        report = ProjectionReport(
            target=self.name,
            destination=str(destination),
            ownership_mode=self.default_ownership_mode,
            lossiness=LossinessKind.PARTIALLY_LOSSLESS,
            notes=["Launch surface is strictly read-only."],
        )

        files = {
            destination / "resources/manifest.json": {
                "capsule_id": capsule.manifest.capsule_id,
                "target": self.name,
                "profile": profile.profile_name,
            },
            destination / "resources/identity.json": {
                "name": capsule.manifest.name,
            },
            destination / "tools/search-memory.json": {
                "name": "search-memory",
                "mode": "read-only",
            },
        }

        for path, payload in files.items():
            updated = True
            if not options.dry_run:
                updated = write_json_if_changed(path, payload)
            record_artifact(
                report,
                str(path.relative_to(destination)),
                path.name,
                OwnershipMode.MANAGED_FILE,
                updated=updated,
            )

        return report

    def ingest_plan(self, options: AdapterOptions | None = None) -> IngestPlan:
        _ = options
        return IngestPlan(
            target=self.name,
            support=IngestSupport.READ_ONLY,
            summary="The starter MCP surface is read-only and does not support ingest.",
            notes=[
                "Promoting MCP-originating changes requires a future governed mutation protocol."
            ],
        )

    def ingest(
        self,
        source_root: Path,
        capsule_root: Path,
        options: AdapterOptions | None = None,
    ) -> IngestReport:
        _ = capsule_root
        plan = self.ingest_plan(options)
        return run_ingest_plan(source_root, plan, options)
