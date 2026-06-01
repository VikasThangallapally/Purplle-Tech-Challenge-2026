from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from pipeline import video_reader
from pipeline.video_reader import VideoReader


@dataclass
class FakeCapture:
    frames: list[object]
    fps: float = 25.0
    width: int = 1920
    height: int = 1080

    def __post_init__(self) -> None:
        self._index = 0

    def isOpened(self) -> bool:
        return True

    def read(self):
        if self._index >= len(self.frames):
            return False, None
        frame = self.frames[self._index]
        self._index += 1
        return True, frame

    def get(self, prop_id: int):
        if prop_id == 5:  # CAP_PROP_FPS
            return self.fps
        if prop_id == 3:  # CAP_PROP_FRAME_WIDTH
            return self.width
        if prop_id == 4:  # CAP_PROP_FRAME_HEIGHT
            return self.height
        if prop_id == 1:  # CAP_PROP_POS_FRAMES
            return self._index
        if prop_id == 0:  # CAP_PROP_POS_MSEC
            return (self._index / self.fps) * 1000.0 if self.fps else 0.0
        return 0

    def release(self) -> None:
        return None


class FakeCv2:
    CAP_PROP_POS_MSEC = 0
    CAP_PROP_POS_FRAMES = 1
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_FPS = 5

    def __init__(self, mapping: dict[str, list[object]]) -> None:
        self._mapping = mapping

    def VideoCapture(self, path: str) -> FakeCapture:
        return FakeCapture(self._mapping[path])


def test_discover_videos_and_read_frames(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "dataset"
    nested = root / "STORE_BLR_001"
    nested.mkdir(parents=True)
    video_one = nested / "clip_a.mp4"
    video_two = nested / "clip_b.MP4"
    video_one.touch()
    video_two.touch()

    fake_frames = {
        str(video_one): [object(), object()],
        str(video_two): [object()],
    }
    monkeypatch.setattr(video_reader, "cv2", FakeCv2(fake_frames))

    reader = VideoReader()
    discovered = reader.discover_videos(root)
    assert discovered == sorted([video_one, video_two], key=lambda path: str(path).lower())

    frames = list(reader.read_video(video_one))
    assert len(frames) == 2
    assert frames[0].frame_index == 0
    assert frames[0].video_name == "clip_a.mp4"
    assert frames[0].fps == 25.0
    assert frames[0].width == 1920
    assert frames[0].height == 1080
    assert frames[0].timestamp_ms == 40.0
