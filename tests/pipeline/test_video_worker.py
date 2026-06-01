from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.frame import VideoFrame
from pipeline.video_worker import VideoWorker


@dataclass
class StubReader:
    discovered: list[Path]
    frames_by_video: dict[Path, list[VideoFrame]]

    def discover_videos(self, dataset_root):
        return self.discovered

    def read_video(self, video_path):
        yield from self.frames_by_video[video_path]


class StubDetector:
    def __init__(self) -> None:
        self.frames: list[object] = []

    def detect(self, frame: object):
        self.frames.append(frame)
        return []


def test_worker_processes_all_frames_and_reports_summary(tmp_path: Path) -> None:
    video_path = tmp_path / "STORE_BLR_001" / "video.mp4"
    video_path.parent.mkdir(parents=True)
    video_path.touch()

    frame_one = VideoFrame(video_path=video_path, video_name="video.mp4", frame_index=0, timestamp_ms=0.0, fps=30.0, width=640, height=480, image=object())
    frame_two = VideoFrame(video_path=video_path, video_name="video.mp4", frame_index=1, timestamp_ms=33.3, fps=30.0, width=640, height=480, image=object())

    reader = StubReader(discovered=[video_path], frames_by_video={video_path: [frame_one, frame_two]})
    detector = StubDetector()
    worker = VideoWorker(reader=reader, detector=detector)

    summary = worker.run(tmp_path)

    assert summary.processed_frames == 2
    assert len(summary.discovered_videos) == 1
    assert len(summary.video_reports) == 1
    assert detector.frames == [frame_one.image, frame_two.image]
    rendered = summary.render()
    assert "Discovered videos: 1" in rendered
    assert "Processed frames: 2" in rendered
