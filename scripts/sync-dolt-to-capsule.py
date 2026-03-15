#!/usr/bin/env python3
"""Sync recent Dolt-Postgres shared memory entries into OAC capsule memory."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Allow importing from fleet's agent package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "fleet"))

from agent.dolt import DoltClient


def sync() -> None:
    capsule_memory = Path(__file__).resolve().parent.parent / "examples/vertigo-embodiment/memory"
    capsule_memory.mkdir(parents=True, exist_ok=True)

    try:
        client = DoltClient()
        conn = client._conn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM shared_memory ORDER BY ts DESC LIMIT 50")
            entries = cur.fetchall()
        conn.close()
    except Exception as e:
        print(f"Dolt unavailable: {e}, skipping sync")
        return

    if not entries:
        print("No entries to sync")
        return

    # Group by date
    by_date: dict[str, list[dict]] = {}
    for entry in entries:
        dt = datetime.datetime.fromtimestamp(entry["ts"])
        day = dt.strftime("%Y-%m-%d")
        by_date.setdefault(day, []).append(entry)

    # Write daily memory files
    for day, day_entries in by_date.items():
        path = capsule_memory / f"{day}.md"
        lines = [f"---\nkind: memory.episodic\nsummary: Experiences from {day}\n---\n\n"]
        for e in day_entries:
            lines.append(f"- [{e['machine']}/{e['agent_id']}] {e['content']}\n")
        path.write_text("".join(lines))

    print(f"Synced {len(entries)} entries across {len(by_date)} days")


if __name__ == "__main__":
    sync()
