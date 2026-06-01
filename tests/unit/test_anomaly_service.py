from datetime import datetime, timedelta, timezone

from retail_intelligence.application.services.anomaly_service import AnomalyService
from retail_intelligence.domain.entities.anomaly import ZoneLastActivity
from retail_intelligence.domain.entities.event import Event


class FakeAnomalyRepository:
    def __init__(self, events: list[Event], zone_activity: list[ZoneLastActivity]) -> None:
        self._events = events
        self._zone_activity = zone_activity

    def list_events_since(self, store_id: int, since: datetime):
        return [event for event in self._events if event.store_id == store_id and event.timestamp >= since]

    def list_zone_last_activity(self, store_id: int):
        return [activity for activity in self._zone_activity if True]


def test_detects_queue_spike_conversion_drop_and_dead_zone() -> None:
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)

    events = [
        Event("e1", 1, None, "v1", "queue_joined", yesterday.replace(hour=9), "billing_queue", None, False, 0.9, {}),
        Event("e2", 1, None, "v2", "person_entered", yesterday.replace(hour=9, minute=5), "SKINCARE", None, False, 0.9, {}),
        Event("e3", 1, None, "v2", "purchase", yesterday.replace(hour=9, minute=10), "checkout", None, False, 0.9, {}),
        Event("e4", 1, None, "v3", "queue_joined", today.replace(hour=9), "billing_queue", None, False, 0.9, {}),
        Event("e5", 1, None, "v4", "queue_joined", today.replace(hour=9, minute=1), "billing_queue", None, False, 0.9, {}),
        Event("e6", 1, None, "v5", "queue_joined", today.replace(hour=9, minute=2), "billing_queue", None, False, 0.9, {}),
        Event("e7", 1, None, "v6", "queue_joined", today.replace(hour=9, minute=3), "billing_queue", None, False, 0.9, {}),
        Event("e8", 1, None, "v7", "queue_joined", today.replace(hour=9, minute=4), "billing_queue", None, False, 0.9, {}),
    ]
    zone_activity = [
        ZoneLastActivity("SKINCARE", now - timedelta(minutes=31)),
        ZoneLastActivity("BILLING", now - timedelta(minutes=10)),
    ]

    service = AnomalyService(FakeAnomalyRepository(events, zone_activity))
    response = service.detect(1)

    anomaly_types = {item.type for item in response.anomalies}
    assert "QUEUE_SPIKE" in anomaly_types
    assert "CONVERSION_DROP" in anomaly_types
    assert "DEAD_ZONE" in anomaly_types
