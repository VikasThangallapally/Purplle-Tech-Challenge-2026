from collections.abc import Sequence

from sqlalchemy.orm import Session

from retail_intelligence.application.services.event_service import EventService
from retail_intelligence.infrastructure.db.repositories.event_repository_impl import EventRepositoryImpl
from retail_intelligence.schemas.event import EventIngestItem, EventIngestResponse


class EventIngestService:
    def __init__(self, db: Session) -> None:
        self._event_repository = EventRepositoryImpl(db)
        self._event_service = EventService(self._event_repository)

    def validate_events(self, events: Sequence[EventIngestItem]) -> list[EventIngestItem]:
        return self._event_service.validate_events(events)

    def ingest_events(self, events: Sequence[EventIngestItem]) -> EventIngestResponse:
        return self._event_service.ingest_events(events)
