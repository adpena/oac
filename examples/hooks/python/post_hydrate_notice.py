"""Small example hook used by starter adapter profiles.

This script intentionally does something boring: it prints a JSON note that a hydrate step
completed. Real users can replace it with notifications, index refreshes, or environment-
specific automation once they opt in via a copied adapter profile.
"""

from __future__ import annotations

import json


def main() -> int:
    payload = {
        "event": "post-hydrate",
        "tool": "oac",
        "status": "ok",
        "note": "starter hook placeholder",
    }
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
