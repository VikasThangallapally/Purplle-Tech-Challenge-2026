from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from retail_intelligence.domain.entities.detection import Detection


@dataclass(slots=True)
class TrackedDetection:
    track_id: str
    detection: Detection
    first_seen_at: datetime
    last_seen_at: datetime
    matched: bool = True

    @property
    def camera_id(self) -> int:
        return self.detection.camera_id


@dataclass(slots=True)
class ReidentifiedTrack:
    track_id: str
    visitor_id: str
    detection: Detection
    embedding: tuple[float, ...] = field(default_factory=tuple)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


@dataclass(slots=True)
class ZoneRegion:
    zone_id: str
    name: str
    zone_type: str
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(slots=True)
class ZoneAssignment:
    track_id: str
    visitor_id: str
    detection: Detection
    zone_id: str | None
    zone_type: str | None
    first_seen_at: datetime
    last_seen_at: datetime

    @property
    def dwell_ms(self) -> int:
        return max(0, int((self.last_seen_at - self.first_seen_at).total_seconds() * 1000))


@dataclass(slots=True)
class QueueSnapshot:
    store_id: int
    queue_depth: int
    average_queue_depth: float
    is_spike: bool
    queue_track_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PipelineResult:
    detections: list[Detection]
    tracks: list[TrackedDetection]
    reidentified_tracks: list[ReidentifiedTrack]
    zone_assignments: list[ZoneAssignment]
    queue_snapshot: QueueSnapshot
    events: list[dict[str, Any]]
