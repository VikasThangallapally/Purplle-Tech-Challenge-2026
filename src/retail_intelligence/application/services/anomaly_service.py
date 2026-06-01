from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from retail_intelligence.domain.entities.anomaly import ZoneLastActivity
from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.repositories.anomaly_repository import AnomalyRepository
from retail_intelligence.infrastructure.db.repositories.anomaly_repository_impl import AnomalyRepositoryImpl
from retail_intelligence.schemas.analytics import AnomalyItem, AnomalyResponse


QUEUE_EVENT_TYPES = {"billing_queue", "queue_joined", "queue_entered", "queue"}
PURCHASE_EVENT_TYPES = {"purchase", "checkout_completed", "transaction_completed"}
DEAD_ZONE_THRESHOLD_MINUTES = 30


class AnomalyService:
    def __init__(self, repository: AnomalyRepository) -> None:
        self._repository = repository

    @classmethod
    def from_session(cls, db) -> "AnomalyService":
        return cls(AnomalyRepositoryImpl(db))

    def detect(self, store_id: int) -> AnomalyResponse:
        now = datetime.now(timezone.utc)
        events = list(self._repository.list_events_since(store_id, now - timedelta(days=8)))
        zone_last_activity = list(self._repository.list_zone_last_activity(store_id))

        anomalies: list[AnomalyItem] = []

        queue_spike = self._detect_queue_spike(events, now)
        if queue_spike is not None:
            anomalies.append(queue_spike)

        conversion_drop = self._detect_conversion_drop(events, now)
        if conversion_drop is not None:
            anomalies.append(conversion_drop)

        anomalies.extend(self._detect_dead_zones(zone_last_activity, now))

        return AnomalyResponse(store_id=str(store_id), anomalies=anomalies)

    def _detect_queue_spike(self, events: list[Event], now: datetime) -> AnomalyItem | None:
        grouped = self._group_events_by_day(events)
        if not grouped:
            return None

        current_day = now.date()
        current_events = grouped.get(current_day, [])
        historical_days = [day for day in grouped if day < current_day]
        historical_depths = [self._queue_depth_for_events(grouped[day]) for day in historical_days]
        if not historical_depths:
            return None

        historical_average = sum(historical_depths) / len(historical_depths)
        if historical_average <= 0:
            return None

        current_queue_depth = self._queue_depth_for_events(current_events)
        if current_queue_depth > 2 * historical_average:
            return AnomalyItem(
                type="QUEUE_SPIKE",
                severity="WARN",
                message=(
                    f"Current queue depth {current_queue_depth} exceeds 2x historical average "
                    f"{historical_average:.2f}"
                ),
                suggested_action="Open additional billing counters",
                detected_at=now.isoformat(),
            )
        return None

    def _detect_conversion_drop(self, events: list[Event], now: datetime) -> AnomalyItem | None:
        grouped = self._group_events_by_day(events)
        if not grouped:
            return None

        current_day = now.date()
        current_events = grouped.get(current_day, [])
        current_conversion = self._conversion_rate(current_events)

        historical_days = [day for day in grouped if day < current_day]
        historical_rates = [self._conversion_rate(grouped[day]) for day in historical_days]
        if not historical_rates:
            return None

        historical_average = sum(historical_rates) / len(historical_rates)
        if historical_average <= 0:
            return None

        if current_conversion < 0.7 * historical_average:
            return AnomalyItem(
                type="CONVERSION_DROP",
                severity="CRITICAL",
                message=(
                    f"Today's conversion rate {current_conversion:.2f}% is below 70% of the "
                    f"7-day average {historical_average:.2f}%"
                ),
                suggested_action="Investigate store operations and staffing",
                detected_at=now.isoformat(),
            )
        return None

    def _detect_dead_zones(self, zone_last_activity: list[ZoneLastActivity], now: datetime) -> list[AnomalyItem]:
        anomalies: list[AnomalyItem] = []
        threshold = timedelta(minutes=DEAD_ZONE_THRESHOLD_MINUTES)

        for activity in zone_last_activity:
            if now - activity.last_seen_at > threshold:
                anomalies.append(
                    AnomalyItem(
                        type="DEAD_ZONE",
                        severity="INFO",
                        message=(
                            f"Zone {activity.zone_id} has no visits for more than "
                            f"{DEAD_ZONE_THRESHOLD_MINUTES} minutes"
                        ),
                        suggested_action="Review product placement or promotions",
                        detected_at=now.isoformat(),
                    )
                )

        return anomalies

    def _group_events_by_day(self, events: list[Event]) -> dict[date, list[Event]]:
        grouped: dict[date, list[Event]] = defaultdict(list)
        for event in events:
            timestamp = event.timestamp.astimezone(timezone.utc)
            grouped[timestamp.date()].append(event)
        return grouped

    def _queue_depth_for_events(self, events: list[Event]) -> int:
        latest_by_visitor: dict[str, Event] = {}
        for event in sorted(events, key=lambda item: item.timestamp):
            if event.visitor_id:
                latest_by_visitor[event.visitor_id] = event

        return sum(1 for event in latest_by_visitor.values() if self._is_queue_event(event))

    def _conversion_rate(self, events: list[Event]) -> float:
        visitors = {event.visitor_id for event in events if event.visitor_id and not event.is_staff}
        if not visitors:
            return 0.0

        purchase_visitors = {
            event.visitor_id
            for event in events
            if event.visitor_id and event.event_type.lower() in PURCHASE_EVENT_TYPES and not event.is_staff
        }
        return round((len(purchase_visitors) / len(visitors)) * 100.0, 2)

    def _is_queue_event(self, event: Event) -> bool:
        if event.event_type.lower() in QUEUE_EVENT_TYPES:
            return True
        if event.zone_id is not None and "queue" in event.zone_id.lower():
            return True
        return False
