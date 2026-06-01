from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from retail_intelligence.domain.entities.detection import Detection
from retail_intelligence.infrastructure.vision.state import TrackedDetection

logger = logging.getLogger(__name__)


class ByteTrackTracker:
    def __init__(self, iou_threshold: float = 0.3, max_age_frames: int = 30) -> None:
        self._iou_threshold = iou_threshold
        self._max_age_frames = max_age_frames
        self._tracks: dict[int, list[_TrackState]] = defaultdict(list)
        self._counter = 0

    def track(self, detections: list[Detection], timestamp: datetime | None = None) -> list[TrackedDetection]:
        now = timestamp or datetime.now(timezone.utc)
        tracked: list[TrackedDetection] = []

        grouped: dict[int, list[Detection]] = defaultdict(list)
        for detection in detections:
            grouped[detection.camera_id].append(detection)

        for camera_id, camera_detections in grouped.items():
            active_tracks = self._tracks[camera_id]
            active_tracks[:] = [track for track in active_tracks if track.age <= self._max_age_frames]

            matched_track_ids: set[str] = set()
            for detection in camera_detections:
                track_state = self._match_track(active_tracks, detection)
                if track_state is None:
                    self._counter += 1
                    track_id = f"track-{self._counter:05d}"
                    track_state = _TrackState(track_id=track_id, detection=detection, last_seen_at=now, first_seen_at=now)
                    active_tracks.append(track_state)
                else:
                    track_state.detection = detection
                    track_state.last_seen_at = now
                    track_state.age = 0

                matched_track_ids.add(track_state.track_id)
                tracked.append(
                    TrackedDetection(
                        track_id=track_state.track_id,
                        detection=detection,
                        first_seen_at=track_state.first_seen_at,
                        last_seen_at=track_state.last_seen_at,
                    )
                )

            for track_state in active_tracks:
                if track_state.track_id not in matched_track_ids:
                    track_state.age += 1

            logger.debug("Tracked detections for camera", extra={"camera_id": camera_id, "track_count": len(camera_detections)})

        return tracked

    def _match_track(self, active_tracks: list[_TrackState], detection: Detection) -> _TrackState | None:
        best_track: _TrackState | None = None
        best_iou = 0.0
        for track_state in active_tracks:
            iou = self._iou(track_state.detection.bbox, detection.bbox)
            if iou > best_iou:
                best_iou = iou
                best_track = track_state

        if best_iou < self._iou_threshold:
            return None
        return best_track

    def _iou(self, left, right) -> float:
        x1 = max(left.x1, right.x1)
        y1 = max(left.y1, right.y1)
        x2 = min(left.x2, right.x2)
        y2 = min(left.y2, right.y2)

        intersection_width = max(0.0, x2 - x1)
        intersection_height = max(0.0, y2 - y1)
        intersection_area = intersection_width * intersection_height

        left_area = max(0.0, left.width) * max(0.0, left.height)
        right_area = max(0.0, right.width) * max(0.0, right.height)
        union_area = left_area + right_area - intersection_area
        if union_area <= 0:
            return 0.0
        return intersection_area / union_area


PersonTracker = ByteTrackTracker



class _TrackState:
    def __init__(self, track_id: str, detection: Detection, first_seen_at: datetime, last_seen_at: datetime) -> None:
        self.track_id = track_id
        self.detection = detection
        self.first_seen_at = first_seen_at
        self.last_seen_at = last_seen_at
        self.age = 0

