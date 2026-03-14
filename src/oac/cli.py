from __future__ import annotations

import argparse
import json
from pathlib import Path

from oac.ack import render_ack_report, run_adapter_ack
from oac.adapter_utils import load_effective_profile
from oac.adapters import AdapterOptions, get_adapter
from oac.catalog import get_target, list_targets, render_target_description
from oac.evals import eval_report_to_dict, evaluate_capsule, render_eval_report
from oac.hooks import run_hooks
from oac.index import (
    generate_lexical_index,
    generate_structural_index,
    write_lexical_index,
    write_structural_index,
)
from oac.ingest import ingest_report_to_dict, render_ingest_plan
from oac.io import validate_manifest
from oac.mcp import serve_mcp
from oac.models import FORMAT_POLICIES
from oac.profile_io import scaffold_profile, validate_profile
from oac.profile_models import HookPhase
from oac.proposals import (
    MergePolicy,
    create_proposal_bundle,
    load_proposal_bundle,
    merge_proposal_bundles,
    preview_promotion,
    promotion_report_to_dict,
    proposal_bundle_to_dict,
    render_conflicts,
    render_proposal_bundle,
    revert_promotion,
    revert_report_to_dict,
    write_proposal_bundle,
)
from oac.publish import publish_snapshot
from oac.snapshot import create_snapshot, snapshot_report_to_dict
from oac.workflows import create_promotion_workflow, write_workflow


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

    ack_cmd = subparsers.add_parser("ack", help="Run the Adapter Conformance Kit")
    ack_cmd.add_argument("target", help="Harness target name")
    ack_cmd.add_argument("capsule", type=Path, help="Path to capsule root")

    targets_cmd = subparsers.add_parser("targets", help="List supported agent harness targets")
    targets_cmd.add_argument("--verbose", action="store_true", help="Show target summaries")

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
    hydrate.add_argument(
        "--kind",
        action="append",
        dest="kinds",
        help="Filter by record kind; may be supplied multiple times",
    )
    hydrate.add_argument("--dry-run", action="store_true", help="Report without writing files")
    hydrate.add_argument("--no-hooks", action="store_true", help="Disable hook execution")

    ingest = subparsers.add_parser("ingest", help="Scan a native target projection into candidates")
    ingest.add_argument("target", help="Harness target name")
    ingest.add_argument("source", type=Path, help="Projected target root to scan")
    ingest.add_argument("capsule", type=Path, help="Path to capsule root")
    ingest.add_argument("--profile", type=Path, help="Optional custom adapter profile")
    ingest.add_argument("--state", type=str, help="Optional path to an incremental state file")
    ingest.add_argument("--json", action="store_true", help="Emit full report as JSON")
    ingest.add_argument("--no-hooks", action="store_true", help="Disable hook execution")

    propose = subparsers.add_parser("propose", help="Turn ingest candidates into proposal records")
    propose.add_argument("target", help="Harness target name")
    propose.add_argument("source", type=Path, help="Projected target root to scan")
    propose.add_argument("capsule", type=Path, help="Path to capsule root")
    propose.add_argument("--profile", type=Path, help="Optional custom adapter profile")
    propose.add_argument("--state", type=str, help="Optional path to an incremental state file")
    propose.add_argument("--output", type=Path, help="Optional JSON output path")
    propose.add_argument("--json", action="store_true", help="Emit full proposal bundle as JSON")
    propose.add_argument("--no-hooks", action="store_true", help="Disable hook execution")

    merge_proposals = subparsers.add_parser(
        "merge-proposals", help="Merge multiple proposal bundles and detect conflicts"
    )
    merge_proposals.add_argument(
        "proposals", type=Path, nargs="+", help="Paths to proposal JSON files"
    )
    merge_proposals.add_argument("--output", type=Path, help="Optional JSON output path")
    merge_proposals.add_argument(
        "--resolve",
        type=str,
        choices=[p.value for p in MergePolicy],
        default=MergePolicy.FAIL.value,
        help="Conflict resolution policy",
    )
    merge_proposals.add_argument(
        "--json", action="store_true", help="Emit full merged bundle as JSON"
    )

    conflicts = subparsers.add_parser("conflicts", help="Show detailed conflicts in a bundle")
    conflicts.add_argument("proposal", type=Path, help="Path to proposal bundle JSON")

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
    revert.add_argument(
        "--force",
        action="store_true",
        help="Force revert even if files were modified after promotion",
    )
    revert.add_argument("--json", action="store_true", help="Emit full revert report as JSON")

    snapshot = subparsers.add_parser("snapshot", help="Create a local tar.gz capsule snapshot")
    snapshot.add_argument("capsule", type=Path, help="Path to capsule root")
    snapshot.add_argument(
        "output", type=Path, help="Directory where snapshot artifacts are written"
    )
    snapshot.add_argument(
        "--sign-key", type=Path, help="Optional path to a secret key file to sign the snapshot"
    )
    snapshot.add_argument("--json", action="store_true", help="Emit full snapshot report as JSON")

    publish = subparsers.add_parser(
        "publish-snapshot", help="Publish a snapshot to a registry layout"
    )
    publish.add_argument("capsule", type=Path, help="Path to capsule root")
    publish.add_argument("publish_root", type=Path, help="Directory for the registry layout")
    publish.add_argument(
        "--sign-key", type=Path, help="Optional path to a secret key file to sign the snapshot"
    )
    publish.add_argument("--json", action="store_true", help="Emit full publish report as JSON")

    subparsers.add_parser("policy", help="Show current OAC format and compatibility policies")

    conformance = subparsers.add_parser(
        "conformance",
        help="Run hydrate+ingest conformance across enabled targets",
    )
    conformance.add_argument("capsule", type=Path, help="Path to capsule root")
    conformance.add_argument(
        "--json", action="store_true", help="Emit full conformance report as JSON"
    )

    index = subparsers.add_parser("index", help="Generate a lexical index for the capsule")
    index.add_argument("capsule", type=Path, help="Path to capsule root")
    index.add_argument("output", type=Path, help="Path to write the index JSON")

    struct_index = subparsers.add_parser(
        "structural-index", help="Generate a structural index for the capsule"
    )
    struct_index.add_argument("capsule", type=Path, help="Path to capsule root")
    struct_index.add_argument("output", type=Path, help="Path to write the structural index JSON")

    serve_mcp_cmd = subparsers.add_parser("serve-mcp", help="Start the OAC MCP server")
    serve_mcp_cmd.add_argument("capsule", type=Path, help="Path to capsule root")

    workflow = subparsers.add_parser("workflow", help="Manage a promotion workflow")
    workflow.add_argument("proposal", type=Path, help="Path to proposal bundle JSON")
    workflow.add_argument("output", type=Path, help="Path to write the workflow JSON")

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


def cmd_ack(target: str, capsule: Path) -> int:
    get_target(target)
    report = run_adapter_ack(target, capsule)
    print(render_ack_report(report))
    return 0 if report.passed else 1


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
    kinds: list[str] | None,
    dry_run: bool,
    no_hooks: bool = False,
) -> int:
    get_target(target)
    adapter = get_adapter(target)
    report = adapter.hydrate(
        capsule_root=capsule,
        destination=output,
        options=AdapterOptions(
            dry_run=dry_run,
            profile_path=str(profile) if profile else None,
            record_kinds=kinds,
            enable_hooks=not no_hooks,
        ),
    )
    print(f"hydrated: {report.target}")
    print(f"destination: {report.destination}")
    print(f"lossiness: {report.lossiness.value}")
    if report.updated_count > 0 or report.unchanged_count > 0:
        print(f"updated: {report.updated_count}")
        print(f"unchanged: {report.unchanged_count}")
    for artifact in report.artifacts:
        print(f"- {artifact.path} [{artifact.ownership_mode.value}]")

    # Run post-hydrate hooks
    if not no_hooks:
        profile_obj = load_effective_profile(target, str(profile) if profile else None)
        hook_results = run_hooks(
            profile_obj,
            HookPhase.POST_HYDRATE,
            context={
                "capsule": str(capsule),
                "output": str(output),
                "artifacts": [a.path for a in report.artifacts],
            },
        )
        for res in hook_results:
            status = "ok" if res.success else f"failed ({res.exit_code})"
            print(f"hook: {res.name} -> {status}")
            if not res.success:
                print(f"  stderr: {res.stderr}")

    return 0


def _run_ingest(
    target: str,
    source: Path,
    capsule: Path,
    profile: Path | None,
    state: str | None,
    no_hooks: bool = False,
):
    get_target(target)
    adapter = get_adapter(target)
    return adapter.ingest(
        source_root=source,
        capsule_root=capsule,
        options=AdapterOptions(
            profile_path=str(profile) if profile else None,
            incremental_state_path=state,
            enable_hooks=not no_hooks,
        ),
    )


def cmd_ingest(
    target: str,
    source: Path,
    capsule: Path,
    profile: Path | None,
    state: str | None,
    json_output: bool,
    no_hooks: bool = False,
) -> int:
    report = _run_ingest(target, source, capsule, profile, state, no_hooks)
    if json_output:
        print(json.dumps(ingest_report_to_dict(report), indent=2, sort_keys=False))
        return 0

    print(f"ingested: {report.target}")
    print(f"source: {report.source_root}")
    print(f"support: {report.support.value}")
    print(f"matched: {report.stats.matched_paths}")
    print(f"candidates: {report.stats.candidate_count}")
    if report.stats.unchanged_count > 0:
        print(f"unchanged: {report.stats.unchanged_count}")
    for candidate in report.candidates:
        print(f"- {candidate.kind}: {candidate.source_path} -> {candidate.candidate_path_hint}")
    for note in report.notes:
        print(f"note: {note}")

    # Run post-ingest hooks
    if not no_hooks:
        profile_obj = load_effective_profile(target, str(profile) if profile else None)
        hook_results = run_hooks(
            profile_obj,
            HookPhase.POST_INGEST,
            context={
                "source": str(source),
                "capsule": str(capsule),
                "candidates": [c.candidate_id for c in report.candidates],
            },
        )
        for res in hook_results:
            status = "ok" if res.success else f"failed ({res.exit_code})"
            print(f"hook: {res.name} -> {status}")
            if not res.success:
                print(f"  stderr: {res.stderr}")

    return 0


def cmd_propose(
    target: str,
    source: Path,
    capsule: Path,
    profile: Path | None,
    state: str | None,
    output: Path | None,
    json_output: bool,
    no_hooks: bool = False,
) -> int:
    ingest_report = _run_ingest(target, source, capsule, profile, state, no_hooks)
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


def cmd_merge_proposals(
    proposals: list[Path], resolve: str, output: Path | None, json_output: bool
) -> int:
    bundles = [load_proposal_bundle(p) for p in proposals]
    merged = merge_proposal_bundles(bundles, policy=MergePolicy(resolve))
    if output:
        write_proposal_bundle(merged, output)
    if json_output:
        print(json.dumps(proposal_bundle_to_dict(merged), indent=2, sort_keys=False))
        return 0

    print(render_proposal_bundle(merged))
    if output:
        print(f"wrote merged proposal bundle: {output}")
    return 0


def cmd_conflicts(proposal: Path) -> int:
    bundle = load_proposal_bundle(proposal)
    print(render_conflicts(bundle))
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


def cmd_revert(promotion: Path, capsule: Path, apply: bool, force: bool, json_output: bool) -> int:
    try:
        report = revert_promotion(promotion, capsule, apply=apply, force=force)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=False))
        else:
            print(f"error: {exc}")
        return 1
    if json_output:
        print(json.dumps(revert_report_to_dict(report), indent=2, sort_keys=False))
        return 0
    print(f"revert: {report.promotion_id}")
    print(f"reverted: {report.reverted_count}")
    print(f"restored: {report.restored_count}")
    print(f"deleted: {report.deleted_count}")
    return 0


def cmd_snapshot(capsule: Path, output: Path, sign_key: Path | None, json_output: bool) -> int:
    report = create_snapshot(capsule, output, sign_key=sign_key)
    if json_output:
        print(json.dumps(snapshot_report_to_dict(report), indent=2, sort_keys=False))
        return 0
    print(f"snapshot: {report.snapshot_id}")
    print(f"archive: {report.archive_path}")
    print(f"files: {report.file_count}")
    if report.signature_path:
        print(f"signature: {report.signature_path}")
    return 0


def cmd_publish_snapshot(
    capsule: Path, publish_root: Path, sign_key: Path | None, json_output: bool
) -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        snap_report = create_snapshot(capsule, Path(tmp_dir), sign_key=sign_key)
        pub_report = publish_snapshot(snap_report, publish_root)

    if json_output:
        payload = {
            "capsule_id": pub_report.capsule_id,
            "snapshot_id": pub_report.snapshot_id,
            "publish_root": pub_report.publish_root,
            "archive_name": pub_report.archive_name,
            "notes": pub_report.notes,
        }
        print(json.dumps(payload, indent=2, sort_keys=False))
        return 0

    print(f"published: {pub_report.capsule_id} ({pub_report.snapshot_id})")
    print(f"registry: {pub_report.publish_root}")
    return 0


def cmd_policy() -> int:
    print("OAC Format and Compatibility Policies")
    print("-" * 40)
    for kind, policy in FORMAT_POLICIES.items():
        print(f"{kind}:")
        print(f"  current: {policy.current}")
        print(f"  minimum: {policy.minimum}")
        print(f"  supported: {', '.join(policy.supported)}")
    return 0


def cmd_index(capsule: Path, output: Path) -> int:
    index = generate_lexical_index(capsule)
    write_lexical_index(index, output)
    print(f"index: {index.capsule_id}")
    print(f"keywords: {len(index.keywords)}")
    print(f"output: {output}")
    return 0


def cmd_structural_index(capsule: Path, output: Path) -> int:
    index = generate_structural_index(capsule)
    write_structural_index(index, output)
    print(f"structural-index: {index.capsule_id}")
    print(f"kinds: {len(index.kinds)}")
    print(f"tags: {len(index.tags)}")
    print(f"output: {output}")
    return 0


def cmd_serve_mcp(capsule: Path) -> int:
    import sys

    print(f"Starting OAC MCP server for capsule at {capsule}...", file=sys.stderr)
    serve_mcp(capsule)
    return 0


def cmd_workflow(proposal: Path, output: Path) -> int:
    bundle = load_proposal_bundle(proposal)
    workflow = create_promotion_workflow(proposal, bundle.capsule_id)
    write_workflow(workflow, output)
    print(f"workflow: {workflow.workflow_id}")
    print(f"status: {workflow.status.value}")
    print(f"output: {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args.path)
    if args.command == "validate-profile":
        return cmd_validate_profile(args.path)
    if args.command == "ack":
        return cmd_ack(args.target, args.capsule)
    if args.command == "targets":
        return cmd_targets(verbose=args.verbose)
    if args.command == "describe-target":
        return cmd_describe_target(args.target)
    if args.command == "describe-ingest":
        return cmd_describe_ingest(args.target, args.profile)
    if args.command == "scaffold-profile":
        return cmd_scaffold_profile(args.target, args.output)
    if args.command == "hydrate":
        return cmd_hydrate(
            args.target,
            args.capsule,
            args.output,
            args.profile,
            args.kinds,
            args.dry_run,
            args.no_hooks,
        )
    if args.command == "ingest":
        return cmd_ingest(
            args.target,
            args.source,
            args.capsule,
            args.profile,
            args.state,
            args.json,
            args.no_hooks,
        )
    if args.command == "propose":
        return cmd_propose(
            args.target,
            args.source,
            args.capsule,
            args.profile,
            args.state,
            args.output,
            args.json,
            args.no_hooks,
        )
    if args.command == "merge-proposals":
        return cmd_merge_proposals(args.proposals, args.resolve, args.output, args.json)
    if args.command == "conflicts":
        return cmd_conflicts(args.proposal)
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
        return cmd_revert(args.promotion, args.capsule, args.apply, args.force, args.json)
    if args.command == "snapshot":
        return cmd_snapshot(args.capsule, args.output, args.sign_key, args.json)
    if args.command == "publish-snapshot":
        return cmd_publish_snapshot(args.capsule, args.publish_root, args.sign_key, args.json)
    if args.command == "policy":
        return cmd_policy()
    if args.command == "conformance":
        return cmd_eval(args.capsule, None, None, args.json, mode="conformance")
    if args.command == "index":
        return cmd_index(args.capsule, args.output)
    if args.command == "structural-index":
        return cmd_structural_index(args.capsule, args.output)
    if args.command == "serve-mcp":
        return cmd_serve_mcp(args.capsule)
    if args.command == "workflow":
        return cmd_workflow(args.proposal, args.output)

    parser.error(f"Unknown command: {args.command}")
    return 2
