from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    import cv2
except ImportError:  # pragma: no cover - exercised only when OpenCV is not installed
    cv2 = None  # type: ignore[assignment]

from pipeline.frame import VideoFrame


@dataclass(slots=True)
class VideoMetadata:
    fps: float
    width: int
    height: int


class VideoReader:
    def discover_videos(self, dataset_root: Path | str) -> list[Path]:
        root = Path(dataset_root)
        if not root.exists():
            return []
        videos = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".mp4"]
        return sorted(videos, key=lambda path: str(path).lower())

    def read_video(self, video_path: Path | str) -> Iterator[VideoFrame]:
        if cv2 is None:
            raise RuntimeError("OpenCV is required to read MP4 videos")

        path = Path(video_path)
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise RuntimeError(f"Could not open video: {path}")

        try:
            metadata = self._read_metadata(capture)
            frame_index = 0
            while True:
                success, frame = capture.read()
                if not success:
                    break

                timestamp_ms = self._timestamp_ms(capture, frame_index, metadata.fps)
                width, height = self._frame_size(frame, metadata.width, metadata.height)
                yield VideoFrame(
                    video_path=path,
                    video_name=path.name,
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                    fps=metadata.fps,
                    width=width,
                    height=height,
                    image=frame,
                )
                frame_index += 1
        finally:
            capture.release()

    def read_dataset(self, dataset_root: Path | str) -> Iterator[VideoFrame]:
        for video_path in self.discover_videos(dataset_root):
            yield from self.read_video(video_path)

    def _read_metadata(self, capture: Any) -> VideoMetadata:
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        return VideoMetadata(fps=fps, width=width, height=height)

    def _timestamp_ms(self, capture: Any, frame_index: int, fps: float) -> float:
        timestamp_ms = float(capture.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
        if timestamp_ms > 0.0:
            return timestamp_ms
        if fps > 0.0:
            return (frame_index / fps) * 1000.0
        return float(frame_index)

    def _frame_size(self, frame: Any, default_width: int, default_height: int) -> tuple[int, int]:
        width = default_width
        height = default_height
        shape = getattr(frame, "shape", None)
        if shape is not None and len(shape) >= 2:
            height = int(shape[0]) or height
            width = int(shape[1]) or width
        return width, height
