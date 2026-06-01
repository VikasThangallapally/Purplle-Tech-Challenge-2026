"""Validate generated events in outputs/events/events.jsonl and print report."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

EV_PATH = Path("outputs/events/events.jsonl")


def load_events(path: Path) -> List[Dict]:
    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def key_of(ev: Dict) -> Tuple[int, str]:
    return (int(ev.get("visitor_id")), ev.get("camera_id"))


def main() -> None:
    if not EV_PATH.exists():
        print("No events file found:", EV_PATH)
        return

    events = load_events(EV_PATH)
    print(f"Total events: {len(events)}")

    entries = [e for e in events if e.get("event_type") == "ENTRY"]
    exits = [e for e in events if e.get("event_type") == "EXIT"]
    print(f"Total Entries: {len(entries)}")
    print(f"Total Exits: {len(exits)}")

    print("\nFirst 20 events:")
    for e in events[:20]:
        print(json.dumps(e, ensure_ascii=False))

    # Duplicates per (visitor_id, camera_id)
    def find_duplicates(ev_list: List[Dict]):
        counts: Dict[Tuple[int,str], int] = {}
        for e in ev_list:
            k = key_of(e)
            counts[k] = counts.get(k, 0) + 1
        dup = {k: c for k, c in counts.items() if c > 1}
        return dup

    dup_entries = find_duplicates(entries)
    dup_exits = find_duplicates(exits)

    # Validate: iterate events in file order to ensure EXIT has prior ENTRY
    seen_entries: set[Tuple[int, str]] = set()
    exit_without_entry = []
    ts_violations = []
    prev_ts = None
    last_event_by_key: Dict[Tuple[int, str], Dict] = {}

    for i, e in enumerate(events):
        k = key_of(e)
        ts = float(e.get("timestamp", 0))
        # timestamp non-decreasing check
        if prev_ts is not None and ts < prev_ts:
            ts_violations.append((i, prev_ts, ts, e))
        prev_ts = ts

        if e.get("event_type") == "ENTRY":
            seen_entries.add(k)
        elif e.get("event_type") == "EXIT":
            if k not in seen_entries:
                exit_without_entry.append(e)

        last_event_by_key[k] = e

    # Active visitors: keys where last event is ENTRY
    active = [k for k, ev in last_event_by_key.items() if ev.get("event_type") == "ENTRY"]

    print("\nValidation Report:")
    print("- Duplicate ENTRY events:", "PASS" if not dup_entries else "FAIL")
    if dup_entries:
        for k, c in dup_entries.items():
            print(f"  {k}: {c} entries")

    print("- Duplicate EXIT events:", "PASS" if not dup_exits else "FAIL")
    if dup_exits:
        for k, c in dup_exits.items():
            print(f"  {k}: {c} exits")

    print("- EXIT has corresponding ENTRY:", "PASS" if not exit_without_entry else "FAIL")
    if exit_without_entry:
        print("  Exits without prior entry (showing up to 10):")
        for ex in exit_without_entry[:10]:
            print("   ", json.dumps(ex, ensure_ascii=False))

    print("- Event timestamps increasing:", "PASS" if not ts_violations else "FAIL")
    if ts_violations:
        for idx, prev, cur, ev in ts_violations[:10]:
            print(f"  at index {idx}: previous={prev}, current={cur}, event={ev.get('event_id')}")

    print(f"\nEvent summary: Total Entries={len(entries)}, Total Exits={len(exits)}, Active Visitors={len(active)}")


if __name__ == "__main__":
    main()
