from __future__ import annotations

import logging
import math

from retail_intelligence.infrastructure.vision.state import ReidentifiedTrack, TrackedDetection

logger = logging.getLogger(__name__)


class OSNetReIdentifier:
    def __init__(self, similarity_threshold: float = 0.92) -> None:
        self._similarity_threshold = similarity_threshold
        self._gallery: dict[str, tuple[float, ...]] = {}
        self._counter = 0

    def identify(self, tracks: list[TrackedDetection]) -> list[ReidentifiedTrack]:
        identified: list[ReidentifiedTrack] = []
        for track in tracks:
            embedding = self._embedding(track)
            visitor_id = self._find_match(embedding)
            if visitor_id is None:
                self._counter += 1
                visitor_id = f"visitor-{self._counter:05d}"
            self._gallery[visitor_id] = embedding
            identified.append(
                ReidentifiedTrack(
                    track_id=track.track_id,
                    visitor_id=visitor_id,
                    detection=track.detection,
                    embedding=embedding,
                    first_seen_at=track.first_seen_at,
                    last_seen_at=track.last_seen_at,
                )
            )
        logger.debug("Re-identified tracks", extra={"count": len(identified)})
        return identified

    def _find_match(self, embedding: tuple[float, ...]) -> str | None:
        best_match: str | None = None
        best_similarity = 0.0
        for visitor_id, candidate_embedding in self._gallery.items():
            similarity = self._cosine_similarity(embedding, candidate_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = visitor_id
        if best_similarity >= self._similarity_threshold:
            return best_match
        return None

    def _embedding(self, track: TrackedDetection) -> tuple[float, ...]:
        bbox = track.detection.bbox
        width = max(1.0, bbox.width)
        height = max(1.0, bbox.height)
        center_x = (bbox.x1 + bbox.x2) / 2.0
        center_y = (bbox.y1 + bbox.y2) / 2.0
        return (
            round(center_x / width, 4),
            round(center_y / height, 4),
            round(width / 1000.0, 4),
            round(height / 1000.0, 4),
            round(track.detection.confidence, 4),
        )

    def _cosine_similarity(self, left: tuple[float, ...], right: tuple[float, ...]) -> float:
        numerator = sum(l * r for l, r in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)


PersonReIdentifier = OSNetReIdentifier


