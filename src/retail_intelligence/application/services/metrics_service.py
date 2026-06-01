from collections.abc import Sequence

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.repositories.store_analytics_repository import StoreAnalyticsRepository
from retail_intelligence.infrastructure.db.repositories.store_analytics_repository_impl import StoreAnalyticsRepositoryImpl
from retail_intelligence.schemas.metrics import StoreMetricsResponse


PURCHASE_EVENT_TYPES = {"purchase", "checkout_completed", "transaction_completed"}
QUEUE_EVENT_TYPES = {"billing_queue", "queue_joined", "queue_entered"}
ENTRY_EVENT_TYPES = {"entry", "person_entered", "store_entry", "entered"}


class MetricsService:
    def __init__(self, repository: StoreAnalyticsRepository) -> None:
        self._repository = repository

    @classmethod
    def from_session(cls, db) -> "MetricsService":
        return cls(StoreAnalyticsRepositoryImpl(db))

    def get_metrics(self, store_id: int) -> StoreMetricsResponse:
        events = list(self._repository.list_store_events(store_id))
        unique_visitors = self._unique_visitors(events)
        purchase_visitors = self._purchase_visitors(events)
        queue_visitors = self._queue_visitors(events)
        avg_dwell_time = self._average_dwell_time(events)
        queue_depth = self._queue_depth(events)

        conversion_rate = self._percentage(len(purchase_visitors), len(unique_visitors))
        abandonment_rate = self._percentage(len(queue_visitors - purchase_visitors), len(queue_visitors))

        return StoreMetricsResponse(
            store_id=store_id,
            unique_visitors=len(unique_visitors),
            conversion_rate=conversion_rate,
            avg_dwell_time=avg_dwell_time,
            queue_depth=queue_depth,
            abandonment_rate=abandonment_rate,
        )

    def _unique_visitors(self, events: Sequence[Event]) -> set[str]:
        return {event.visitor_id for event in events if event.visitor_id}

    def _purchase_visitors(self, events: Sequence[Event]) -> set[str]:
        return {
            event.visitor_id
            for event in events
            if event.visitor_id and event.event_type.lower() in PURCHASE_EVENT_TYPES
        }

    def _queue_visitors(self, events: Sequence[Event]) -> set[str]:
        return {
            event.visitor_id
            for event in events
            if event.visitor_id
            and (
                event.event_type.lower() in QUEUE_EVENT_TYPES
                or (event.zone_id is not None and "queue" in event.zone_id.lower())
            )
        }

    def _average_dwell_time(self, events: Sequence[Event]) -> float:
        dwell_values = [event.dwell_ms for event in events if event.dwell_ms is not None]
        if not dwell_values:
            return 0.0
        return round(sum(dwell_values) / len(dwell_values) / 1000.0, 2)

    def _queue_depth(self, events: Sequence[Event]) -> int:
        latest_by_visitor: dict[str, Event] = {}
        for event in events:
            if event.visitor_id:
                latest_by_visitor[event.visitor_id] = event
        return sum(
            1
            for event in latest_by_visitor.values()
            if event.event_type.lower() in QUEUE_EVENT_TYPES
            or (event.zone_id is not None and "queue" in event.zone_id.lower())
        )

    def _percentage(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 2)