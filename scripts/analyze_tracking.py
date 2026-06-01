from __future__ import annotations
import json
from pathlib import Path
from statistics import mean

INPUT = Path("outputs/tracking/tracking_results.json")
OUTPUT = Path("outputs/tracking/analysis_report.json")
FRAME_RATE = 30.0  # assumed

EDGE_RATIO = 0.10  # 10% of image width/height considered "edge"

if not INPUT.exists():
    raise SystemExit(f"Missing input report: {INPUT}")

data = json.loads(INPUT.read_text(encoding="utf-8"))
summary = {"videos": []}

for vid in data:
    frames = vid["frames"]
    if not frames:
        continue
    # infer frame size from first bbox max values when available
    # fallback width/height guess
    width = 1920
    height = 1080
    # collect track presence
    tracks = {}
    for f in frames:
        fn = f["frame_number"]
        for det in f["detections"]:
            tid = int(det["track_id"])
            bbox = det["bbox"]
            if tid not in tracks:
                tracks[tid] = {"frames": [], "bboxes": []}
            tracks[tid]["frames"].append(fn)
            tracks[tid]["bboxes"].append(bbox)
            # try to update width/height estimates
            if bbox:
                maxx = max(maxx:=bbox[2], bbox[0])
                maxy = max(maxy:=bbox[3], bbox[1])
                if maxx and maxx > width:
                    width = int(maxx)
                if maxy and maxy > height:
                    height = int(maxy)

    total_unique = len(tracks)
    durations = []
    lost = []
    entries = []
    exits = []

    left = right = top = bottom = center = 0
    exit_left = exit_right = exit_top = exit_bottom = exit_center = 0

    for tid, info in tracks.items():
        first = min(info["frames"])
        last = max(info["frames"])
        dur = last - first + 1
        durations.append(dur)
        if last < vid.get("frames_processed", last):
            lost.append(tid)
        # entry point
        fb = info["bboxes"][0]
        cx = (fb[0] + fb[2]) / 2.0
        cy = (fb[1] + fb[3]) / 2.0
        if cx <= EDGE_RATIO * width:
            left += 1
            entries.append((tid, "left"))
        elif cx >= (1 - EDGE_RATIO) * width:
            right += 1
            entries.append((tid, "right"))
        elif cy <= EDGE_RATIO * height:
            top += 1
            entries.append((tid, "top"))
        elif cy >= (1 - EDGE_RATIO) * height:
            bottom += 1
            entries.append((tid, "bottom"))
        else:
            center += 1
            entries.append((tid, "center"))
        # exit point
        lb = info["bboxes"][-1]
        cx2 = (lb[0] + lb[2]) / 2.0
        cy2 = (lb[1] + lb[3]) / 2.0
        if cx2 <= EDGE_RATIO * width:
            exit_left += 1
            exits.append((tid, "left"))
        elif cx2 >= (1 - EDGE_RATIO) * width:
            exit_right += 1
            exits.append((tid, "right"))
        elif cy2 <= EDGE_RATIO * height:
            exit_top += 1
            exits.append((tid, "top"))
        elif cy2 >= (1 - EDGE_RATIO) * height:
            exit_bottom += 1
            exits.append((tid, "bottom"))
        else:
            exit_center += 1
            exits.append((tid, "center"))

    avg_dur_frames = mean(durations) if durations else 0
    avg_dur_seconds = avg_dur_frames / FRAME_RATE

    video_summary = {
        "video_filename": vid.get("video_filename"),
        "frames_processed": vid.get("frames_processed"),
        "total_unique_track_ids": total_unique,
        "average_track_duration_frames": avg_dur_frames,
        "average_track_duration_seconds": round(avg_dur_seconds, 2),
        "new_tracks_created": total_unique,
        "lost_tracks": len(lost),
        "lost_track_ids": lost,
        "entry_counts": {"left": left, "right": right, "top": top, "bottom": bottom, "center": center},
        "entries": entries,
        "exit_counts": {"left": exit_left, "right": exit_right, "top": exit_top, "bottom": exit_bottom, "center": exit_center},
        "exits": exits,
    }
    summary["videos"].append(video_summary)

# High-level missing items for event generation
missing = [
    "per-frame timestamps (to compute absolute times)",
    "camera intrinsics / homography to map bbox -> world coordinates",
    "store zone polygons (named zones) with coordinates in image or world space",
    "camera calibration / unified coordinate system across cameras for re-entry detection",
    "consistent frame rate / exact video start time",
    "robust re-identification across cameras (appearance features) for true REENTRY",
    "zone occupancy thresholds and dwell time thresholds for ZONE_DWELL",
    "entry/exit portal definitions and tolerances (threshold distances from border)",
]
summary["requirements_for_events"] = missing

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("Wrote analysis to:", OUTPUT)
print(json.dumps(summary, indent=2))
