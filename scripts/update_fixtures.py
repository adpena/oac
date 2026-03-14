from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oac.adapters import AdapterOptions, get_adapter  # noqa: E402
from oac.ingest import ingest_report_to_dict  # noqa: E402
from oac.proposals import create_proposal_bundle, proposal_bundle_to_dict  # noqa: E402

EXAMPLE = ROOT / "examples" / "hello-capsule"
PROJECTION_FIXTURES = ROOT / "tests" / "fixtures" / "projections"
INGEST_FIXTURES = ROOT / "tests" / "fixtures" / "ingest"
PROPOSAL_FIXTURES = ROOT / "tests" / "fixtures" / "proposals"
TARGETS = ["codex", "openclaw", "claude-code", "opencode", "gemini", "mcp", "webmcp"]


def main() -> None:
    PROJECTION_FIXTURES.mkdir(parents=True, exist_ok=True)
    INGEST_FIXTURES.mkdir(parents=True, exist_ok=True)
    PROPOSAL_FIXTURES.mkdir(parents=True, exist_ok=True)
    for target in TARGETS:
        projection_destination = PROJECTION_FIXTURES / target
        if projection_destination.exists():
            shutil.rmtree(projection_destination)
        adapter = get_adapter(target)
        adapter.hydrate(EXAMPLE, projection_destination, AdapterOptions())
        print(f"updated projection fixture: {target}")

        ingest_report = adapter.ingest(projection_destination, EXAMPLE, AdapterOptions())
        ingest_path = INGEST_FIXTURES / f"{target}.json"
        ingest_path.write_text(
            json.dumps(ingest_report_to_dict(ingest_report), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        print(f"updated ingest fixture: {ingest_path}")

        proposal_bundle = create_proposal_bundle(EXAMPLE, ingest_report)
        proposal_path = PROPOSAL_FIXTURES / f"{target}.json"
        proposal_path.write_text(
            json.dumps(proposal_bundle_to_dict(proposal_bundle), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        print(f"updated proposal fixture: {proposal_path}")


if __name__ == "__main__":
    main()
