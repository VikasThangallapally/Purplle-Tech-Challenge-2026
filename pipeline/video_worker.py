from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Protocol

from pipeline.frame import VideoFrame
from pipeline.video_reader import VideoReader

logger = logging.getLogger(__name__)


class FrameDetector(Protocol):
    def detect(self, frame: object) -> object: ...


class NoOpDetector:
    def detect(self, frame: object) -> list[object]:
        return []


@dataclass(slots=True)
class VideoRunReport:
    video_name: str
    video_path: Path
    frames_processed: int
    fps: float
    width: int
    height: int


@dataclass(slots=True)
class WorkerSummary:
    discovered_videos: list[Path] = field(default_factory=list)
    video_reports: list[VideoRunReport] = field(default_factory=list)
    processed_frames: int = 0

    @property
    def fps_values(self) -> list[float]:
        return [report.fps for report in self.video_reports if report.fps > 0]

    def render(self) -> str:
        lines = [f"Discovered videos: {len(self.discovered_videos)}", f"Processed frames: {self.processed_frames}"]
        if self.fps_values:
            lines.append(
                "FPS statistics: "
                f"min={min(self.fps_values):.2f}, "
                f"max={max(self.fps_values):.2f}, "
                f"avg={mean(self.fps_values):.2f}"
            )
        else:
            lines.append("FPS statistics: unavailable")
        for report in self.video_reports:
            lines.append(
                f"- {report.video_name}: frames={report.frames_processed}, fps={report.fps:.2f}, "
                f"size={report.width}x{report.height}"
            )
        return "\n".join(lines)


class VideoWorker:
    def __init__(self, reader: VideoReader | None = None, detector: FrameDetector | None = None) -> None:
        self._reader = reader or VideoReader()
        self._detector = detector or NoOpDetector()

    def run(self, dataset_root: Path | str) -> WorkerSummary:
        discovered_videos = self._reader.discover_videos(dataset_root)
        summary = WorkerSummary(discovered_videos=discovered_videos)

        for video_path in discovered_videos:
            video_report = self._process_video(video_path)
            summary.video_reports.append(video_report)
            summary.processed_frames += video_report.frames_processed

        return summary

    def _process_video(self, video_path: Path) -> VideoRunReport:
        frames_processed = 0
        fps = 0.0
        width = 0
        height = 0

        for frame in self._reader.read_video(video_path):
            fps = frame.fps
            width = frame.width
            height = frame.height
            frames_processed += 1

            logger.info(
                "Processed video frame",
                extra={
                    "video_name": frame.video_name,
                    "frame_number": frame.frame_index,
                    "timestamp": frame.timestamp_ms,
                },
            )
            self._detector.detect(frame.image)

        return VideoRunReport(
            video_name=video_path.name,
            video_path=video_path,
            frames_processed=frames_processed,
            fps=fps,
            width=width,
            height=height,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the video ingestion worker")
    parser.add_argument("--dataset-root", required=True, help="Root folder containing raw MP4 videos")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    worker = VideoWorker()
    summary = worker.run(args.dataset_root)
    print(summary.render())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
