from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
from ultralytics import YOLO


DEFAULT_VIDEO_ROOT = Path("data/raw_videos")
FALLBACK_VIDEO_ROOT = Path("CCTV Footage-20260529T160731Z-3-00144614ea/CCTV Footage")
OUTPUT_ROOT = Path("outputs/debug")
REPORT_PATH = OUTPUT_ROOT / "cctv_detection_results.json"


def find_first_video(root: Path) -> Path | None:
    if not root.exists():
        return None
    videos = sorted(root.rglob("*.mp4"))
    return videos[0] if videos else None


def find_videos(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.mp4"))


def load_first_frame(video_path: Path) -> tuple[cv2.VideoCapture, object]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    success, frame = capture.read()
    if not success or frame is None:
        capture.release()
        raise RuntimeError(f"Unable to read first frame from: {video_path}")

    return capture, frame


def draw_detections(frame: object, detections: list[dict[str, object]]) -> object:
    annotated = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = (int(v) for v in detection["bbox"])
        confidence = float(detection["confidence"])
        label = f"person {confidence:.2f}"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    return annotated


def run_detection(video_path: Path, model: YOLO) -> dict[str, object]:
    capture, frame = load_first_frame(video_path)
    try:
        height, width = frame.shape[:2]
        results = model.predict(source=frame, verbose=False)

        detections: list[dict[str, object]] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            xyxy = boxes.xyxy.tolist() if hasattr(boxes.xyxy, "tolist") else list(boxes.xyxy)
            conf = boxes.conf.tolist() if hasattr(boxes.conf, "tolist") else list(boxes.conf)
            cls = boxes.cls.tolist() if hasattr(boxes.cls, "tolist") else list(boxes.cls)

            for bbox, confidence, class_id in zip(xyxy, conf, cls):
                if int(class_id) != 0:
                    continue
                detections.append(
                    {
                        "bbox": bbox[:4],
                        "confidence": float(confidence),
                    }
                )

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        video_output_path = OUTPUT_ROOT / f"{video_path.stem}_detection.jpg"
        annotated = draw_detections(frame, detections)
        if not cv2.imwrite(str(video_output_path), annotated):
            raise RuntimeError(f"Failed to save annotated image to: {video_output_path}")

        return {
            "video_filename": video_path.name,
            "video_path": str(video_path),
            "frame_width": width,
            "frame_height": height,
            "people_detected": len(detections),
            "detections": detections,
            "annotated_image": str(video_output_path),
        }
    finally:
        capture.release()


def print_result(result: dict[str, object]) -> None:
    print(f"video filename: {result['video_filename']}")
    print(f"frame dimensions: {result['frame_width']}x{result['frame_height']}")
    print(f"number of people detected: {result['people_detected']}")
    for index, detection in enumerate(result["detections"], start=1):
        bbox = detection["bbox"]
        confidence = float(detection["confidence"])
        print(f"detection {index}: confidence={confidence:.4f}, bbox={[round(float(value), 2) for value in bbox]}")
    print(f"saved annotated image: {result['annotated_image']}")


def run_all_videos(video_paths: list[Path]) -> list[dict[str, object]]:
    if not video_paths:
        raise RuntimeError("No MP4 files found to process")

    model = YOLO("yolo11n.pt")
    results: list[dict[str, object]] = []

    for video_path in video_paths:
        try:
            result = run_detection(video_path, model)
        except Exception as exc:
            result = {
                "video_filename": video_path.name,
                "video_path": str(video_path),
                "error": str(exc),
                "people_detected": 0,
                "detections": [],
                "annotated_image": None,
            }
            print(f"[ERROR] {video_path.name}: {exc}", file=sys.stderr)
        else:
            print_result(result)

        results.append(result)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"saved report: {REPORT_PATH}")
    return results


def main() -> int:
    video_paths = find_videos(DEFAULT_VIDEO_ROOT)
    if not video_paths:
        fallback_paths = find_videos(FALLBACK_VIDEO_ROOT)
        if fallback_paths:
            print(f"[WARN] No MP4 files found under {DEFAULT_VIDEO_ROOT}; using fallback footage at {FALLBACK_VIDEO_ROOT}")
            video_paths = fallback_paths

    if not video_paths:
        print(f"[ERROR] No MP4 files found under {DEFAULT_VIDEO_ROOT} or {FALLBACK_VIDEO_ROOT}", file=sys.stderr)
        return 1

    try:
        run_all_videos(video_paths)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())