from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timezone

from retail_intelligence.infrastructure.vision.state import ReidentifiedTrack, ZoneAssignment, ZoneRegion

logger = logging.getLogger(__name__)


class ZoneMapper:
    def __init__(self, zones: Sequence[ZoneRegion] | None = None) -> None:
        self._zones = list(zones or [])

    def map(self, tracks: list[ReidentifiedTrack], timestamp: datetime | None = None) -> list[ZoneAssignment]:
        now = timestamp or datetime.now(timezone.utc)
        assignments: list[ZoneAssignment] = []
        for track in tracks:
            zone = self._match_zone(track)
            assignments.append(
                ZoneAssignment(
                    track_id=track.track_id,
                    visitor_id=track.visitor_id,
                    detection=track.detection,
                    zone_id=zone.zone_id if zone else None,
                    zone_type=zone.zone_type if zone else None,
                    first_seen_at=track.first_seen_at or now,
                    last_seen_at=track.last_seen_at or now,
                )
            )
        logger.debug("Mapped zones for tracks", extra={"count": len(assignments)})
        return assignments

    def _match_zone(self, track: ReidentifiedTrack) -> ZoneRegion | None:
        center_x = (track.detection.bbox.x1 + track.detection.bbox.x2) / 2.0
        center_y = (track.detection.bbox.y1 + track.detection.bbox.y2) / 2.0

        for zone in self._zones:
            if zone.x1 <= center_x <= zone.x2 and zone.y1 <= center_y <= zone.y2:
                return zone
        return None

