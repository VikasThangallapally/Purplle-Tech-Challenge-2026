from sqlalchemy.orm import Session

from retail_intelligence.application.services.event_ingest_service import EventIngestService
from retail_intelligence.schemas.event import EventIngestItem, EventIngestResponse


class IngestEventUseCase:
    def __init__(self, db: Session) -> None:
        self._service = EventIngestService(db)

    def execute(self, payload: list[EventIngestItem]) -> EventIngestResponse:
        return self._service.ingest_events(payload)
