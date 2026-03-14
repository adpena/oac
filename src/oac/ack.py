from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from oac.adapters import AdapterOptions, get_adapter
from oac.proposals import ProposalDisposition, create_proposal_bundle


@dataclass(slots=True)
class ACKCheck:
    name: str
    passed: bool
    summary: str


@dataclass(slots=True)
class AdapterConformanceReport:
    target: str
    passed: bool
    checks: list[ACKCheck] = field(default_factory=list)


def run_adapter_ack(target: str, capsule_root: Path) -> AdapterConformanceReport:
    """Run the Adapter Conformance Kit against a target harness."""
    adapter = get_adapter(target)
    report = AdapterConformanceReport(target=target, passed=True)

    with tempfile.TemporaryDirectory(prefix=f"oac-ack-{target}-") as temp_dir:
        dest = Path(temp_dir) / target

        # 2. Hydrate
        try:
            hydrate_report = adapter.hydrate(capsule_root, dest, AdapterOptions())
            report.checks.append(
                ACKCheck("hydration", True, f"Emitted {len(hydrate_report.artifacts)} artifacts")
            )
        except Exception as exc:
            report.checks.append(ACKCheck("hydration", False, str(exc)))
            report.passed = False
            return report

        # 3. Ingest
        try:
            ingest_report = adapter.ingest(dest, capsule_root, AdapterOptions())
            report.checks.append(
                ACKCheck("ingest", True, f"Discovered {len(ingest_report.candidates)} candidates")
            )
        except Exception as exc:
            report.checks.append(ACKCheck("ingest", False, str(exc)))
            report.passed = False
            return report

        # 4. Round-trip Lossless Check
        bundle = create_proposal_bundle(capsule_root, ingest_report)

        # We check specific canonical kinds that MUST be supported
        required_kinds = {
            "identity.display",
            "identity.persona",
            "user.model",
            "memory.semantic",
        }
        found_kinds = {
            r.canonical_kind
            for r in bundle.records
            if r.disposition in {ProposalDisposition.PROMOTABLE, ProposalDisposition.NOOP}
        }

        missing = required_kinds - found_kinds
        if missing:
            msg = f"Target failed to recover: {', '.join(missing)}"
            report.checks.append(ACKCheck("lossless-coverage", False, msg))
            report.passed = False
        else:
            msg = "All required canonical kinds were recovered in round-trip"
            report.checks.append(ACKCheck("lossless-coverage", True, msg))

    return report


def render_ack_report(report: AdapterConformanceReport) -> str:
    lines = [
        f"ACK: {report.target}",
        f"passed: {'yes' if report.passed else 'no'}",
    ]
    for check in report.checks:
        status = "pass" if check.passed else "fail"
        lines.append(f"- {status}: {check.name} -> {check.summary}")
    return "\n".join(lines)
