from __future__ import annotations

import argparse
import json
from pathlib import Path

from oac.adapters import AdapterOptions, get_adapter
from oac.catalog import get_target, list_targets, render_target_description
from oac.evals import eval_report_to_dict, evaluate_capsule, render_eval_report
from oac.ingest import ingest_report_to_dict, render_ingest_plan
from oac.io import validate_manifest
from oac.profile_io import scaffold_profile, validate_profile
from oac.proposals import (
    create_proposal_bundle,
    load_proposal_bundle,
    preview_promotion,
    promotion_report_to_dict,
    proposal_bundle_to_dict,
    render_proposal_bundle,
    revert_promotion,
    revert_report_to_dict,
    write_proposal_bundle,
)
from oac.snapshot import create_snapshot, snapshot_report_to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oac", description="Open Agent Capsule toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a capsule manifest")
    validate.add_argument("path", type=Path, help="Path to manifest.yaml or a capsule directory")

    validate_profile_cmd = subparsers.add_parser(
        "validate-profile",
        help="Validate an adapter profile",
    )
    validate_profile_cmd.add_argument("path", type=Path, help="Path to adapter profile YAML")

    targets = subparsers.add_parser("targets", help="List known harness targets")
    targets.add_argument("--verbose", action="store_true", help="Show target summaries")

    describe = subparsers.add_parser(
        "describe-target",
        help="Show the bundled profile summary for one target",
    )
    describe.add_argument("target", help="Harness target name")

    describe_ingest = subparsers.add_parser(
        "describe-ingest",
        help="Show the ingest plan summary for one target",
    )
    describe_ingest.add_argument("target", help="Harness target name")
    describe_ingest.add_argument("--profile", type=Path, help="Optional custom adapter profile")

    scaffold = subparsers.add_parser(
        "scaffold-profile",
        help="Write a bundled adapter profile template",
    )
    scaffold.add_argument("target", help="Harness target name")
    scaffold.add_argument("output", type=Path, help="Path to write the adapter profile YAML")

    hydrate = subparsers.add_parser("hydrate", help="Render a native target projection")
    hydrate.add_argument("target", help="Harness target name")
    hydrate.add_argument("capsule", type=Path, help="Path to capsule root")
    hydrate.add_argument("output", type=Path, help="Directory to write the projection")
    hydrate.add_argument("--profile", type=Path, help="Optional custom adapter profile")
    hydrate.add_argument("--dry-run", action="store_true", help="Report without writing files")

    ingest = subparsers.add_parser("ingest", help="Scan a native target projection into candidates")
    ingest.add_argument("target", help="Harness target name")
    ingest.add_argument("source", type=Path, help="Projected target root to scan")
    ingest.add_argument("capsule", type=Path, help="Path to capsule root")
    ingest.add_argument("--profile", type=Path, help="Optional custom adapter profile")
    ingest.add_argument("--json", action="store_true", help="Emit full report as JSON")

    propose = subparsers.add_parser("propose", help="Turn ingest candidates into proposal records")
    propose.add_argument("target", help="Harness target name")
    propose.add_argument("source", type=Path, help="Projected target root to scan")
    propose.add_argument("capsule", type=Path, help="Path to capsule root")
    propose.add_argument("--profile", type=Path, help="Optional custom adapter profile")
    propose.add_argument("--output", type=Path, help="Optional JSON output path")
    propose.add_argument("--json", action="store_true", help="Emit full proposal bundle as JSON")

    eval_cmd = subparsers.add_parser("eval", help="Run the starter structural eval gate")
    eval_cmd.add_argument("capsule", type=Path, help="Path to capsule root")
    eval_cmd.add_argument("--proposal", type=Path, help="Optional proposal bundle JSON")
    eval_cmd.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Optional target filter; may be supplied multiple times",
    )
    eval_cmd.add_argument("--json", action="store_true", help="Emit full eval report as JSON")

    promote = subparsers.add_parser("promote", help="Preview or apply a proposal bundle")
    promote.add_argument("proposal", type=Path, help="Path to proposal bundle JSON")
    promote.add_argument("capsule", type=Path, help="Path to capsule root")
    promote.add_argument(
        "--apply", action="store_true", help="Write promotable changes into the capsule"
    )
    promote.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip the starter eval gate before preview or apply",
    )
    promote.add_argument(
        "--output",
        type=Path,
        help="Optional directory for preview metadata when apply=false",
    )
    promote.add_argument("--json", action="store_true", help="Emit full promotion report as JSON")

    revert = subparsers.add_parser("revert", help="Restore backups from a prior promotion")
    revert.add_argument("promotion", type=Path, help="Path to promotion.json")
    revert.add_argument("capsule", type=Path, help="Path to capsule root")
    revert.add_argument(
        "--apply", action="store_true", help="Apply the revert instead of previewing it"
    )
    revert.add_argument("--json", action="store_true", help="Emit full revert report as JSON")

    snapshot = subparsers.add_parser("snapshot", help="Create a local tar.gz capsule snapshot")
    snapshot.add_argument("capsule", type=Path, help="Path to capsule root")
    snapshot.add_argument(
        "output", type=Path, help="Directory where snapshot artifacts are written"
    )
    snapshot.add_argument("--json", action="store_true", help="Emit full snapshot report as JSON")

    conformance = subparsers.add_parser(
        "conformance",
        help="Run hydrate+ingest conformance across enabled targets",
    )
    conformance.add_argument("capsule", type=Path, help="Path to capsule root")
    conformance.add_argument(
        "--json", action="store_true", help="Emit full conformance report as JSON"
    )

    return parser


def cmd_validate(path: Path) -> int:
    result = validate_manifest(path)
    print(f"valid manifest: {result.capsule_id}")
    print(f"format: {result.format}")
    print(f"targets: {result.target_count}")
    print(f"manifest: {result.manifest_path}")
    return 0


def cmd_validate_profile(path: Path) -> int:
    profile = validate_profile(path)
    print(f"valid profile: {profile.profile_name}")
    print(f"target: {profile.target.value}")
    print(f"surfaces: {len(profile.surfaces)}")
    print(f"flags: {len(profile.flags)}")
    print(f"hooks: {len(profile.hooks)}")
    return 0


def cmd_targets(verbose: bool = False) -> int:
    for entry in list_targets():
        print(entry.target.value)
        if verbose:
            print(f"  title: {entry.title}")
            print(f"  summary: {entry.summary}")
    return 0


def cmd_describe_target(target: str) -> int:
    get_target(target)
    print(render_target_description(target))
    return 0


def cmd_describe_ingest(target: str, profile: Path | None) -> int:
    get_target(target)
    adapter = get_adapter(target)
    plan = adapter.ingest_plan(AdapterOptions(profile_path=str(profile) if profile else None))
    print(render_ingest_plan(plan))
    return 0


def cmd_scaffold_profile(target: str, output: Path) -> int:
    get_target(target)
    path = scaffold_profile(target, output)
    print(f"wrote profile: {path}")
    return 0


def cmd_hydrate(
    target: str,
    capsule: Path,
    output: Path,
    profile: Path | None,
    dry_run: bool,
) -> int:
    get_target(target)
    adapter = get_adapter(target)
    report = adapter.hydrate(
        capsule_root=capsule,
        destination=output,
        options=AdapterOptions(
            dry_run=dry_run,
            profile_path=str(profile) if profile else None,
        ),
    )
    print(f"hydrated: {report.target}")
    print(f"destination: {report.destination}")
    print(f"lossiness: {report.lossiness.value}")
    for artifact in report.artifacts:
        print(f"- {artifact.path} [{artifact.ownership_mode.value}]")
    return 0


def _run_ingest(target: str, source: Path, capsule: Path, profile: Path | None):
    get_target(target)
    adapter = get_adapter(target)
    return adapter.ingest(
        source_root=source,
        capsule_root=capsule,
        options=AdapterOptions(profile_path=str(profile) if profile else None),
    )


def cmd_ingest(
    target: str,
    source: Path,
    capsule: Path,
    profile: Path | None,
    json_output: bool,
) -> int:
    report = _run_ingest(target, source, capsule, profile)
    if json_output:
        print(json.dumps(ingest_report_to_dict(report), indent=2, sort_keys=False))
        return 0

    print(f"ingested: {report.target}")
    print(f"source: {report.source_root}")
    print(f"support: {report.support.value}")
    print(f"candidates: {report.stats.candidate_count}")
    for candidate in report.candidates:
        print(f"- {candidate.kind}: {candidate.source_path} -> {candidate.candidate_path_hint}")
    for note in report.notes:
        print(f"note: {note}")
    return 0


def cmd_propose(
    target: str,
    source: Path,
    capsule: Path,
    profile: Path | None,
    output: Path | None,
    json_output: bool,
) -> int:
    ingest_report = _run_ingest(target, source, capsule, profile)
    bundle = create_proposal_bundle(capsule, ingest_report)
    if output:
        write_proposal_bundle(bundle, output)
    if json_output:
        print(json.dumps(proposal_bundle_to_dict(bundle), indent=2, sort_keys=False))
        return 0

    print(render_proposal_bundle(bundle))
    if output:
        print(f"wrote proposal bundle: {output}")
    return 0


def cmd_eval(
    capsule: Path,
    proposal: Path | None,
    targets: list[str] | None,
    json_output: bool,
    *,
    mode: str = "eval",
) -> int:
    bundle = load_proposal_bundle(proposal) if proposal else None
    report = evaluate_capsule(capsule, bundle, target_names=targets, mode=mode)
    if json_output:
        print(json.dumps(eval_report_to_dict(report), indent=2, sort_keys=False))
        return 0 if report.passed else 1
    print(render_eval_report(report))
    return 0 if report.passed else 1


def cmd_promote(
    proposal: Path,
    capsule: Path,
    apply: bool,
    skip_eval: bool,
    output: Path | None,
    json_output: bool,
) -> int:
    bundle = load_proposal_bundle(proposal)
    eval_passed = True
    if not skip_eval:
        eval_report = evaluate_capsule(capsule, bundle, mode="promotion-eval")
        eval_passed = eval_report.passed
        if not eval_passed:
            if json_output:
                print(json.dumps(eval_report_to_dict(eval_report), indent=2, sort_keys=False))
            else:
                print(render_eval_report(eval_report))
            return 1

    report = preview_promotion(
        bundle,
        capsule,
        apply=apply,
        eval_passed=eval_passed,
        output_root=output,
    )
    if json_output:
        print(json.dumps(promotion_report_to_dict(report), indent=2, sort_keys=False))
        return 0

    print(f"promotion: {report.promotion_id}")
    print(f"applied: {'yes' if report.applied else 'no'}")
    print(f"eval passed: {'yes' if report.eval_passed else 'no'}")
    print(f"changes: {report.change_count}")
    for change in report.changes:
        print(f"- {change.operation.value}: {change.canonical_path}")
    return 0


def cmd_revert(promotion: Path, capsule: Path, apply: bool, json_output: bool) -> int:
    report = revert_promotion(promotion, capsule, apply=apply)
    if json_output:
        print(json.dumps(revert_report_to_dict(report), indent=2, sort_keys=False))
        return 0
    print(f"revert: {report.promotion_id}")
    print(f"reverted: {report.reverted_count}")
    print(f"restored: {report.restored_count}")
    print(f"deleted: {report.deleted_count}")
    return 0


def cmd_snapshot(capsule: Path, output: Path, json_output: bool) -> int:
    report = create_snapshot(capsule, output)
    if json_output:
        print(json.dumps(snapshot_report_to_dict(report), indent=2, sort_keys=False))
        return 0
    print(f"snapshot: {report.snapshot_id}")
    print(f"archive: {report.archive_path}")
    print(f"files: {report.file_count}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args.path)
    if args.command == "validate-profile":
        return cmd_validate_profile(args.path)
    if args.command == "targets":
        return cmd_targets(verbose=args.verbose)
    if args.command == "describe-target":
        return cmd_describe_target(args.target)
    if args.command == "describe-ingest":
        return cmd_describe_ingest(args.target, args.profile)
    if args.command == "scaffold-profile":
        return cmd_scaffold_profile(args.target, args.output)
    if args.command == "hydrate":
        return cmd_hydrate(args.target, args.capsule, args.output, args.profile, args.dry_run)
    if args.command == "ingest":
        return cmd_ingest(args.target, args.source, args.capsule, args.profile, args.json)
    if args.command == "propose":
        return cmd_propose(
            args.target, args.source, args.capsule, args.profile, args.output, args.json
        )
    if args.command == "eval":
        return cmd_eval(args.capsule, args.proposal, args.targets, args.json)
    if args.command == "promote":
        return cmd_promote(
            args.proposal,
            args.capsule,
            args.apply,
            args.skip_eval,
            args.output,
            args.json,
        )
    if args.command == "revert":
        return cmd_revert(args.promotion, args.capsule, args.apply, args.json)
    if args.command == "snapshot":
        return cmd_snapshot(args.capsule, args.output, args.json)
    if args.command == "conformance":
        return cmd_eval(args.capsule, None, None, args.json, mode="conformance")

    parser.error(f"Unknown command: {args.command}")
    return 2
