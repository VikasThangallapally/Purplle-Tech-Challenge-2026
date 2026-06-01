from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.infrastructure.vision.state import QueueSnapshot, ZoneAssignment
from retail_intelligence.schemas.event import EventIngestItem
from retail_intelligence.shared.enums import EventType

logger = logging.getLogger(__name__)


class EventGenerator:
    def __init__(self, dwell_threshold_ms: int = 30000) -> None:
        self._dwell_threshold_ms = dwell_threshold_ms
        self._previous_zone_by_visitor: dict[str, str | None] = {}
        self._first_seen_by_visitor: dict[str, datetime] = {}
        self._last_seen_by_visitor: dict[str, datetime] = {}
        self._previous_assignment_by_visitor: dict[str, ZoneAssignment] = {}

    def generate(self, store_id: int, event_type: str, payload: dict) -> dict:
        timestamp = datetime.now(timezone.utc)
        return {
            "event_id": self._event_id(store_id, EventType(event_type), timestamp, payload.get("track_id", "manual")),
            "store_id": store_id,
            "event_type": event_type,
            "occurred_at": timestamp.isoformat(),
            "payload": payload,
        }

    def generate_events(
        self,
        store_id: int,
        assignments: list[ZoneAssignment],
        queue_snapshot: QueueSnapshot,
        timestamp: datetime | None = None,
    ) -> list[EventIngestItem]:
        now = timestamp or datetime.now(timezone.utc)
        events: list[EventIngestItem] = []

        current_visitors = {assignment.visitor_id for assignment in assignments}
        previous_visitors = set(self._previous_zone_by_visitor)

        current_assignments = {assignment.visitor_id: assignment for assignment in assignments}

        for visitor_id, assignment in current_assignments.items():
            first_seen = self._first_seen_by_visitor.setdefault(visitor_id, assignment.first_seen_at)
            self._last_seen_by_visitor[visitor_id] = assignment.last_seen_at

            if visitor_id not in previous_visitors:
                events.append(self._build_event(store_id, EventType.PERSON_ENTERED, assignment, now, first_seen))

            previous_zone = self._previous_zone_by_visitor.get(visitor_id)
            if previous_zone != assignment.zone_id:
                if assignment.zone_id is not None and "queue" in assignment.zone_id.lower():
                    events.append(self._build_event(store_id, EventType.QUEUE_JOINED, assignment, now, first_seen))
                elif previous_zone is not None and "queue" in previous_zone.lower():
                    events.append(self._build_event(store_id, EventType.QUEUE_LEFT, assignment, now, first_seen))

            if assignment.dwell_ms >= self._dwell_threshold_ms:
                events.append(self._build_event(store_id, EventType.DWELL_STARTED, assignment, now, first_seen))

            self._previous_zone_by_visitor[visitor_id] = assignment.zone_id
            self._previous_assignment_by_visitor[visitor_id] = assignment

        for visitor_id in previous_visitors - current_visitors:
            previous_assignment = self._previous_assignment_by_visitor.pop(visitor_id)
            first_seen = self._first_seen_by_visitor.pop(visitor_id, previous_assignment.first_seen_at)
            self._last_seen_by_visitor.pop(visitor_id, None)
            self._previous_zone_by_visitor.pop(visitor_id, None)
            events.append(self._build_event(store_id, EventType.PERSON_EXITED, previous_assignment, now, first_seen))

        if queue_snapshot.is_spike:
            events.append(
                EventIngestItem(
                    event_id=self._event_id(store_id, EventType.ANOMALY, now, queue_snapshot.queue_depth),
                    store_id=store_id,
                    event_type=EventType.ANOMALY,
                    timestamp=now,
                    zone_id="queue",
                    dwell_ms=None,
                    is_staff=False,
                    confidence=1.0,
                    metadata={
                        "anomaly_type": "QUEUE_SPIKE",
                        "queue_depth": queue_snapshot.queue_depth,
                        "average_queue_depth": queue_snapshot.average_queue_depth,
                    },
                )
            )

        logger.info("Generated vision events", extra={"store_id": store_id, "event_count": len(events)})
        return events

    def _build_event(
        self,
        store_id: int,
        event_type: EventType,
        assignment: ZoneAssignment,
        timestamp: datetime,
        first_seen: datetime,
    ) -> EventIngestItem:
        return EventIngestItem(
            event_id=self._event_id(store_id, event_type, timestamp, assignment.track_id),
            store_id=store_id,
            camera_id=assignment.detection.camera_id,
            visitor_id=assignment.visitor_id,
            event_type=event_type.value,
            timestamp=timestamp,
            zone_id=assignment.zone_id,
            dwell_ms=assignment.dwell_ms,
            is_staff=False,
            confidence=assignment.detection.confidence,
            metadata={
                "track_id": assignment.track_id,
                "first_seen_at": first_seen.isoformat(),
                "last_seen_at": assignment.last_seen_at.isoformat(),
                "zone_type": assignment.zone_type,
            },
        )

    def _event_id(self, store_id: int, event_type: EventType, timestamp: datetime, suffix: object) -> str:
        return f"{store_id}-{event_type.value}-{int(timestamp.timestamp() * 1000)}-{suffix}"

