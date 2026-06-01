import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]


def _exists(path: Path) -> bool:
    return path.exists()


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def validate_videos_and_tracking() -> Dict[str, Any]:
    cctv_root = ROOT / "CCTV Footage-20260529T160731Z-3-00144614ea" / "CCTV Footage"
    mp4_files = list(cctv_root.glob("*.mp4")) if cctv_root.exists() else []

    tracking_path = ROOT / "outputs" / "tracking" / "tracking_results.json"
    tracking_data = _read_json(tracking_path, default=[])
    videos_processed = len(tracking_data) if isinstance(tracking_data, list) else 0
    frames_processed = 0
    if isinstance(tracking_data, list):
        for v in tracking_data:
            frames_processed += int(v.get("frames_processed", 0))

    can_process = len(mp4_files) > 0 and videos_processed > 0 and frames_processed > 0
    return {
        "status": can_process,
        "cctv_mp4_files_found": len(mp4_files),
        "videos_processed": videos_processed,
        "frames_processed": frames_processed,
        "tracking_results_path": str(tracking_path),
    }


def validate_event_files() -> Dict[str, Any]:
    events_path = ROOT / "outputs" / "events" / "events.jsonl"
    zone_events_path = ROOT / "outputs" / "events" / "zone_events.jsonl"

    def count_lines(p: Path) -> int:
        if not p.exists():
            return 0
        with p.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    events_count = count_lines(events_path)
    zone_events_count = count_lines(zone_events_path)
    return {
        "status": events_count > 0 and zone_events_count > 0,
        "events_count": events_count,
        "zone_events_count": zone_events_count,
        "events_path": str(events_path),
        "zone_events_path": str(zone_events_path),
    }


def validate_analytics_files() -> Dict[str, Any]:
    required = [
        ROOT / "outputs" / "analytics" / "journeys.json",
        ROOT / "outputs" / "analytics" / "funnel.json",
        ROOT / "outputs" / "analytics" / "store_metrics.json",
        ROOT / "outputs" / "analytics" / "product_metrics.json",
        ROOT / "outputs" / "analytics" / "conversion_report.json",
        ROOT / "outputs" / "analytics" / "final_pos_analytics_report.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    return {
        "status": len(missing) == 0,
        "required_count": len(required),
        "missing_files": missing,
    }


def validate_dashboard_files() -> Dict[str, Any]:
    required = [
        ROOT / "dashboard" / "app.py",
        ROOT / "src" / "retail_intelligence" / "dashboard" / "streamlit_app.py",
    ]
    missing = [str(p) for p in required if not p.exists()]
    return {
        "status": len(missing) == 0,
        "required_count": len(required),
        "missing_files": missing,
    }


def compute_readiness_score(checks: Dict[str, Dict[str, Any]]) -> int:
    total = len(checks)
    passed = sum(1 for _, c in checks.items() if c.get("status") is True)
    return int(round((passed / total) * 100)) if total > 0 else 0


def main() -> None:
    checks = {
        "videos_and_tracking": validate_videos_and_tracking(),
        "event_files": validate_event_files(),
        "analytics_files": validate_analytics_files(),
        "dashboard_files": validate_dashboard_files(),
    }
    readiness_score = compute_readiness_score(checks)
    missing_items: List[str] = []
    for name, payload in checks.items():
        if payload.get("status") is not True:
            if payload.get("missing_files"):
                missing_items.extend(payload["missing_files"])
            else:
                missing_items.append(name)

    report = {
        "checks": checks,
        "missing_items": missing_items,
        "submission_readiness_score": readiness_score,
    }

    out_path = ROOT / "outputs" / "final_validation_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Validation Summary")
    for name, payload in checks.items():
        print(f"- {name}: {'PASS' if payload.get('status') else 'FAIL'}")
    print("Missing items:", missing_items if missing_items else "None")
    print("Submission readiness score:", readiness_score)
    print("Report written:", out_path)


if __name__ == "__main__":
    main()
