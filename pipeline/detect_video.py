from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.video_reader import VideoReader
from retail_intelligence.infrastructure.vision.detector import YOLODetector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run YOLO detection on a video file")
    parser.add_argument("--video", required=True, help="Path to MP4 video")
    parser.add_argument("--model-path", default="yolo11n.pt", help="Ultralytics model path")
    parser.add_argument("--confidence-threshold", type=float, default=0.5, help="Detection confidence threshold")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    video_path = Path(args.video)
    reader = VideoReader()
    detector = YOLODetector(model_path=args.model_path, confidence_threshold=args.confidence_threshold)

    for frame in reader.read_video(video_path):
        detections = detector.detect(frame.image)
        print(f"video={frame.video_name} frame={frame.frame_index} timestamp_ms={frame.timestamp_ms:.2f} detections={detections}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
