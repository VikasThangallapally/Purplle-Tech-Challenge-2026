from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from retail_intelligence.domain.entities.anomaly import ZoneLastActivity
from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.repositories.anomaly_repository import AnomalyRepository
from retail_intelligence.infrastructure.db.models.event import EventModel


class AnomalyRepositoryImpl(AnomalyRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_events_since(self, store_id: int, since: datetime) -> Sequence[Event]:
        statement = (
            select(EventModel)
            .where(
                EventModel.store_id == store_id,
                EventModel.is_staff.is_(False),
                EventModel.timestamp >= since,
            )
            .order_by(EventModel.timestamp.asc())
        )
        models = self._db.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def list_zone_last_activity(self, store_id: int) -> Sequence[ZoneLastActivity]:
        statement = (
            select(
                EventModel.zone_id.label("zone_id"),
                func.max(EventModel.timestamp).label("last_seen_at"),
            )
            .where(
                EventModel.store_id == store_id,
                EventModel.is_staff.is_(False),
                EventModel.zone_id.is_not(None),
            )
            .group_by(EventModel.zone_id)
        )
        rows = self._db.execute(statement).all()
        return [
            ZoneLastActivity(zone_id=row.zone_id, last_seen_at=row.last_seen_at)
            for row in rows
            if row.zone_id is not None and row.last_seen_at is not None
        ]

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