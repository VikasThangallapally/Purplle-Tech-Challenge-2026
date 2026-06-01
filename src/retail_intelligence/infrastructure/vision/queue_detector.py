from __future__ import annotations

import logging
from collections.abc import Sequence

from retail_intelligence.infrastructure.vision.state import QueueSnapshot, ZoneAssignment

logger = logging.getLogger(__name__)


class QueueDetector:
    def __init__(self, spike_multiplier: float = 2.0) -> None:
        self._spike_multiplier = spike_multiplier
        self._historical_depths: list[int] = []

    def detect_queue(self, store_id: int | Sequence[ZoneAssignment], assignments: Sequence[ZoneAssignment] | None = None) -> QueueSnapshot | int:
        if assignments is None:
            legacy_tracks = list(store_id) if isinstance(store_id, Sequence) else []
            return len(legacy_tracks)

        assert isinstance(store_id, int)
        queue_assignments = [assignment for assignment in assignments if assignment.zone_type == "queue" or assignment.zone_id is not None and "queue" in assignment.zone_id.lower()]
        queue_depth = len(queue_assignments)
        self._historical_depths.append(queue_depth)
        historical_average = sum(self._historical_depths[:-1]) / len(self._historical_depths[:-1]) if len(self._historical_depths) > 1 else 0.0
        is_spike = historical_average > 0.0 and queue_depth > self._spike_multiplier * historical_average

        snapshot = QueueSnapshot(
            store_id=store_id,
            queue_depth=queue_depth,
            average_queue_depth=round(historical_average, 2),
            is_spike=is_spike,
            queue_track_ids=[assignment.track_id for assignment in queue_assignments],
        )
        logger.debug("Detected queue state", extra={"store_id": store_id, "queue_depth": queue_depth, "is_spike": is_spike})
        return snapshot

