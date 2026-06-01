from collections.abc import Sequence
from datetime import datetime, timezone

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.repositories.event_repository import EventRepository
from retail_intelligence.schemas.event import EventIngestItem, EventIngestResponse


class EventService:
    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    def validate_events(self, events: Sequence[EventIngestItem]) -> list[EventIngestItem]:
        validated_events: list[EventIngestItem] = []
        seen_event_ids: set[str] = set()

        for event in events:
            if event.event_id in seen_event_ids:
                raise ValueError(f"Duplicate event_id: {event.event_id}")
            if event.timestamp.tzinfo is None:
                event = event.model_copy(update={"timestamp": event.timestamp.replace(tzinfo=timezone.utc)})
            seen_event_ids.add(event.event_id)
            validated_events.append(event)

        return validated_events

    def ingest_events(self, events: Sequence[EventIngestItem]) -> EventIngestResponse:
        validated_events = self.validate_events(events)
        domain_events = [self._to_domain_event(event) for event in validated_events]
        saved_events = self._event_repository.create_events_batch(domain_events)
        return EventIngestResponse(received=len(events), saved=len(saved_events))

    def _to_domain_event(self, event: EventIngestItem) -> Event:
        return Event(
            event_id=event.event_id,
            store_id=event.store_id,
            camera_id=event.camera_id,
            visitor_id=event.visitor_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            zone_id=event.zone_id,
            dwell_ms=event.dwell_ms,
            is_staff=event.is_staff,
            confidence=event.confidence,
            metadata=event.metadata,
        )