from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class VideoFrame:
    video_path: Path
    video_name: str
    frame_index: int
    timestamp_ms: float
    fps: float
    width: int
    height: int
    image: Any
