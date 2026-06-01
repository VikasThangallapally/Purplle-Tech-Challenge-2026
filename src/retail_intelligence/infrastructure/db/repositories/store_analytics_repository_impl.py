from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.repositories.store_analytics_repository import StoreAnalyticsRepository
from retail_intelligence.infrastructure.db.models.event import EventModel


class StoreAnalyticsRepositoryImpl(StoreAnalyticsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_store_events(self, store_id: int) -> Sequence[Event]:
        statement = (
            select(EventModel)
            .where(
                EventModel.store_id == store_id,
                EventModel.is_staff.is_(False),
                EventModel.visitor_id.is_not(None),
            )
            .order_by(EventModel.visitor_id.asc(), EventModel.timestamp.asc())
        )
        models = self._db.execute(statement).scalars().all()
        return [
            Event(
                event_id=model.event_id,
                store_id=model.store_id,
                camera_id=model.camera_id,
                visitor_id=model.visitor_id,
                event_type=model.event_type,
                timestamp=model.timestamp,
                zone_id=model.zone_id,
                dwell_ms=model.dwell_ms,
                is_staff=model.is_staff,
                confidence=model.confidence,
                metadata=model.event_metadata,
            )
            for model in models
        ]