from collections.abc import Sequence

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.repositories.store_analytics_repository import StoreAnalyticsRepository
from retail_intelligence.infrastructure.db.repositories.store_analytics_repository_impl import StoreAnalyticsRepositoryImpl
from retail_intelligence.schemas.analytics import DropoffPercentages, FunnelResponse


ENTRY_EVENT_TYPES = {"entry", "person_entered", "store_entry", "entered"}
QUEUE_EVENT_TYPES = {"billing_queue", "queue_joined", "queue_entered"}
PURCHASE_EVENT_TYPES = {"purchase", "checkout_completed", "transaction_completed"}


class FunnelService:
    def __init__(self, repository: StoreAnalyticsRepository) -> None:
        self._repository = repository

    @classmethod
    def from_session(cls, db) -> "FunnelService":
        return cls(StoreAnalyticsRepositoryImpl(db))

    def get_funnel(self, store_id: int) -> FunnelResponse:
        events = list(self._repository.list_store_events(store_id))
        entry_visitors = self._entry_visitors(events)
        zone_visitors = self._zone_visitors(events)
        queue_visitors = self._queue_visitors(events)
        purchase_visitors = self._purchase_visitors(events)

        return FunnelResponse(
            store_id=store_id,
            entry=len(entry_visitors),
            zone_visit=len(zone_visitors),
            billing_queue=len(queue_visitors),
            purchase=len(purchase_visitors),
            dropoff_percentages=DropoffPercentages(
                entry_to_zone=self._dropoff(len(entry_visitors), len(zone_visitors)),
                zone_to_queue=self._dropoff(len(zone_visitors), len(queue_visitors)),
                queue_to_purchase=self._dropoff(len(queue_visitors), len(purchase_visitors)),
            ),
        )

    def _entry_visitors(self, events: Sequence[Event]) -> set[str]:
        return {
            event.visitor_id
            for event in events
            if event.visitor_id and event.event_type.lower() in ENTRY_EVENT_TYPES
        }

    def _zone_visitors(self, events: Sequence[Event]) -> set[str]:
        return {
            event.visitor_id
            for event in events
            if event.visitor_id
            and event.zone_id is not None
            and "queue" not in event.zone_id.lower()
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

    def _purchase_visitors(self, events: Sequence[Event]) -> set[str]:
        return {
            event.visitor_id
            for event in events
            if event.visitor_id and event.event_type.lower() in PURCHASE_EVENT_TYPES
        }

    def _dropoff(self, source: int, next_stage: int) -> float:
        if source == 0:
            return 0.0
        return round(((source - next_stage) / source) * 100.0, 2)