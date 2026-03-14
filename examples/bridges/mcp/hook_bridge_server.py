"""Illustrative MCP bridge sketch for exposing hook or capsule status.

This starter intentionally avoids taking an MCP SDK dependency. Replace this placeholder with
an implementation using the official Python, TypeScript, Go, or Rust SDK when you build the
real bridge.
"""

from __future__ import annotations

import json

if __name__ == "__main__":
    payload = {
        "server": "oac-hook-bridge",
        "mode": "read-only",
        "note": "starter MCP bridge placeholder",
    }
    print(json.dumps(payload))
