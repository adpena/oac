from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oac.models import CapsuleManifest  # noqa: E402
from oac.profile_models import AdapterProfile  # noqa: E402

TARGETS = {
    ROOT / "schemas" / "capsule-manifest.schema.json": CapsuleManifest,
    ROOT / "schemas" / "adapter-profile.schema.json": AdapterProfile,
}


def main() -> None:
    for path, model in TARGETS.items():
        schema = model.model_json_schema()
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
