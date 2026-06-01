from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.infrastructure.db.models.event import EventModel


class EventRepositoryImpl:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _to_model(self, event: Event) -> EventModel:
        return EventModel(
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
            event_metadata=event.metadata,
        )

    def _to_domain(self, model: EventModel) -> Event:
        return Event(
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

    def create_event(self, event: Event) -> Event:
        model = self._to_model(event)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def create_events_batch(self, events: Sequence[Event]) -> Sequence[Event]:
        models = [self._to_model(event) for event in events]
        self._db.add_all(models)
        self._db.commit()
        for model in models:
            self._db.refresh(model)
        return [self._to_domain(model) for model in models]

    def get_event_by_id(self, event_id: str) -> Event | None:
        model = self._db.get(EventModel, event_id)
        if model is None:
            return None
        return self._to_domain(model)

    def get_latest_event_timestamp(self) -> datetime | None:
        statement = select(EventModel.timestamp).order_by(EventModel.timestamp.desc()).limit(1)
        return self._db.execute(statement).scalar_one_or_none()
