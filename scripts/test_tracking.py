from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

from pipeline.tracker import PersonTracker
from pipeline.video_reader import VideoReader


DEFAULT_VIDEO_ROOT = Path("data/raw_videos")
FALLBACK_VIDEO_ROOT = Path("CCTV Footage-20260529T160731Z-3-00144614ea/CCTV Footage")
OUTPUT_ROOT = Path("outputs/tracking")
REPORT_PATH = OUTPUT_ROOT / "tracking_results.json"


def find_videos(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.mp4"))


def discover_video_paths(video_root: Path) -> list[Path]:
    video_paths = find_videos(video_root)
    if video_paths:
        return video_paths

    fallback_paths = find_videos(FALLBACK_VIDEO_ROOT)
    if fallback_paths:
        print(f"[WARN] No MP4 files found under {video_root}; using fallback footage at {FALLBACK_VIDEO_ROOT}")
    return fallback_paths


def detect_people(model: YOLO, frame: object) -> list[dict[str, object]]:
    results = model.predict(source=frame, classes=[0], verbose=False)
    detections: list[dict[str, object]] = []

    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue

        xyxy = boxes.xyxy.tolist() if hasattr(boxes.xyxy, "tolist") else list(boxes.xyxy)
        conf = boxes.conf.tolist() if hasattr(boxes.conf, "tolist") else list(boxes.conf)

        for bbox, confidence in zip(xyxy, conf):
            detections.append({"bbox": bbox[:4], "confidence": float(confidence)})

    return detections


def draw_tracks(frame: object, tracks: list[dict[str, object]]) -> object:
    annotated = frame.copy()
    for track in tracks:
        x1, y1, x2, y2 = (int(value) for value in track["bbox"])
        track_id = int(track["track_id"])
        confidence = float(track["confidence"])
        label = f"ID {track_id} {confidence:.2f}"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated,
            label,
            (x1, max(24, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    return annotated


def process_video(video_path: Path, model: YOLO, max_frames: int | None = None) -> dict[str, object]:
    reader = VideoReader()
    tracker = PersonTracker()
    output_dir = OUTPUT_ROOT / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_results: list[dict[str, object]] = []

    for frame_number, frame in enumerate(reader.read_video(video_path), start=1):
        detections = detect_people(model, frame.image)
        tracks = tracker.update(detections)
        track_ids = [int(track["track_id"]) for track in tracks]

        print(f"Frame {frame_number}: Track IDs: {track_ids}")

        annotated = draw_tracks(frame.image, tracks)
        frame_path = output_dir / f"frame_{frame_number:04d}.jpg"
        if not cv2.imwrite(str(frame_path), annotated):
            raise RuntimeError(f"Failed to save annotated frame to: {frame_path}")

        frame_results.append(
            {
                "frame_number": frame_number,
                "timestamp_ms": float(frame.timestamp_ms),
                "fps": float(frame.fps),
                "track_ids": track_ids,
                "detections": tracks,
                "annotated_image": str(frame_path),
            }
        )

        if max_frames is not None and frame_number >= max_frames:
            break

    return {
        "video_filename": video_path.name,
        "video_path": str(video_path),
        "frames_processed": len(frame_results),
        "output_dir": str(output_dir),
        "frames": frame_results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run real YOLO + ByteTrack on CCTV footage")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="Root folder containing raw MP4 videos")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional frame limit per video")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    video_paths = discover_video_paths(video_root)
    if not video_paths:
        print(f"[ERROR] No MP4 files found under {video_root} or {FALLBACK_VIDEO_ROOT}", file=sys.stderr)
        return 1

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    model = YOLO("yolo11n.pt")
    results: list[dict[str, object]] = []

    for video_path in video_paths:
        print(f"Video: {video_path.name}")
        result = process_video(video_path, model, max_frames=args.max_frames)
        results.append(result)

    REPORT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"saved report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())