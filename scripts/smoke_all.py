from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oac.adapters import AdapterOptions, get_adapter  # noqa: E402
from oac.evals import evaluate_capsule  # noqa: E402
from oac.proposals import create_proposal_bundle  # noqa: E402
from oac.snapshot import create_snapshot  # noqa: E402

EXAMPLE = ROOT / "examples" / "hello-capsule"
TARGETS = ["codex", "openclaw", "claude-code", "opencode", "gemini", "mcp", "webmcp"]


def run_smoke(mode: str = "all", *, quiet: bool = False) -> None:
    with tempfile.TemporaryDirectory(prefix="oac-smoke-") as temp_dir:
        root = Path(temp_dir)
        projections: dict[str, Path] = {}
        if mode in {"all", "hydrate", "ingest", "propose"}:
            for target in TARGETS:
                adapter = get_adapter(target)
                destination = root / target
                adapter.hydrate(EXAMPLE, destination, AdapterOptions())
                projections[target] = destination
                if not quiet:
                    print(f"hydrated:{target}")

        if mode in {"all", "ingest", "propose"}:
            for target in TARGETS:
                adapter = get_adapter(target)
                destination = projections[target]
                report = adapter.ingest(destination, EXAMPLE, AdapterOptions())
                if not quiet:
                    print(f"ingested:{target}:{report.stats.candidate_count}")
                if mode in {"all", "propose"}:
                    bundle = create_proposal_bundle(EXAMPLE, report)
                    if not quiet:
                        print(f"proposed:{target}:{bundle.stats.promotable}")

        if mode in {"all", "eval"}:
            eval_report = evaluate_capsule(EXAMPLE, mode="smoke-eval")
            if not eval_report.passed:
                raise SystemExit("eval failed")
            if not quiet:
                print(f"eval:{eval_report.capsule_id}:passed")
            conformance_report = evaluate_capsule(EXAMPLE, mode="smoke-conformance")
            if not conformance_report.passed:
                raise SystemExit("conformance failed")
            if not quiet:
                print(f"conformance:{conformance_report.capsule_id}:passed")
            snapshot_dir = root / "snapshots"
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            snapshot = create_snapshot(EXAMPLE, snapshot_dir)
            if not Path(snapshot.archive_path).exists():
                raise SystemExit("snapshot archive missing")
            if not quiet:
                print(f"snapshot:{snapshot.snapshot_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run starter smoke checks in one process")
    parser.add_argument(
        "--mode",
        choices=["all", "hydrate", "ingest", "propose", "eval"],
        default="all",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    run_smoke(args.mode, quiet=args.quiet)


if __name__ == "__main__":
    main()
