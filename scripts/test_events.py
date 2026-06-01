from __future__ import annotations

import json
from pathlib import Path

from pipeline.event_generator import EventGenerator


def main() -> int:
    tracking_path = Path("outputs/tracking/tracking_results.json")
    if not tracking_path.exists():
        print(f"Tracking results not found: {tracking_path}")
        return 1

    with tracking_path.open("r", encoding="utf-8") as f:
        tracking_results = json.load(f)

    gen = EventGenerator()
    events = gen.generate_from_tracking(tracking_results)

    total_entries = sum(1 for e in events if e.get("event_type") == "ENTRY")
    total_exits = sum(1 for e in events if e.get("event_type") == "EXIT")
    active_visitors = len(gen.sessions.active_sessions())

    summary = {
        "total_events": len(events),
        "total_entries": total_entries,
        "total_exits": total_exits,
        "active_visitors": active_visitors,
    }

    out_dir = Path("outputs/events")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "events_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote events: {out_dir / 'events.jsonl'}")
    print(f"Wrote summary: {out_dir / 'events_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
