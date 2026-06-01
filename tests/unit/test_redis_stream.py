from datetime import datetime, timezone

from retail_intelligence.infrastructure.redis.event_consumer import EventConsumer
from retail_intelligence.infrastructure.redis.event_producer import EventProducer
from retail_intelligence.infrastructure.redis.redis_stream import decode_event, encode_event, store_event_stream_name
from retail_intelligence.schemas.event import EventIngestItem


class FakeRedis:
    def __init__(self) -> None:
        self.streams: dict[str, list[dict[str, str]]] = {}
        self.groups: set[tuple[str, str]] = set()
        self.acked: list[tuple[str, str, tuple[str, ...]]] = []

    def xadd(self, stream_name: str, payload: dict[str, str]) -> str:
        messages = self.streams.setdefault(stream_name, [])
        message_id = f"{len(messages) + 1}-0"
        stored_payload = dict(payload)
        stored_payload["_id"] = message_id
        messages.append(stored_payload)
        return message_id

    def xgroup_create(self, stream_name: str, group_name: str, id: str, mkstream: bool = False):
        self.groups.add((stream_name, group_name))

    def xreadgroup(self, groupname: str, consumername: str, streams: dict[str, str], count: int, block: int):
        results = []
        for stream_name in streams:
            messages = self.streams.get(stream_name, [])[:count]
            if messages:
                results.append((stream_name, [(message["_id"], {key: value for key, value in message.items() if key != "_id"}) for message in messages]))
        return results

    def xack(self, stream_name: str, group_name: str, *message_ids: str):
        self.acked.append((stream_name, group_name, message_ids))


class StubEventRepository:
    def __init__(self) -> None:
        self.saved = []

    def create_events_batch(self, events):
        self.saved.extend(events)
        return list(events)


class StubSession:
    pass


def test_stream_name_per_store() -> None:
    assert store_event_stream_name(17) == "store:17:events"


def test_encode_decode_roundtrip() -> None:
    event = EventIngestItem(
        event_id="evt-1",
        store_id=1,
        camera_id=2,
        visitor_id="visitor-1",
        event_type="person_entered",
        timestamp=datetime.now(timezone.utc),
        zone_id="entrance",
        dwell_ms=1000,
        is_staff=False,
        confidence=0.9,
        metadata={"source": "camera-1"},
    )

    encoded = encode_event(event)
    decoded = decode_event("1-0", encoded)

    assert decoded.event.event_id == event.event_id
    assert decoded.event.metadata == event.metadata


def test_producer_publishes_batched_events_by_store() -> None:
    redis_client = FakeRedis()
    producer = EventProducer(redis_client=redis_client)
    events = [
        EventIngestItem(
            event_id="evt-1",
            store_id=1,
            event_type="person_entered",
            timestamp=datetime.now(timezone.utc),
        ),
        EventIngestItem(
            event_id="evt-2",
            store_id=1,
            event_type="purchase",
            timestamp=datetime.now(timezone.utc),
        ),
    ]

    published_ids = producer.publish_events(events)

    assert len(published_ids) == 2
    assert store_event_stream_name(1) in redis_client.streams


def test_consumer_processes_store_batch() -> None:
    redis_client = FakeRedis()
    event = EventIngestItem(
        event_id="evt-1",
        store_id=1,
        event_type="person_entered",
        timestamp=datetime.now(timezone.utc),
    )
    redis_client.xadd(store_event_stream_name(1), encode_event(event))

    from retail_intelligence.application.services.event_service import EventService

    original_ingest_events = EventService.ingest_events

    def fake_ingest_events(self, events):
        return type("Result", (), {"received": len(events), "saved": len(events)})()

    EventService.ingest_events = fake_ingest_events
    try:
        consumer = EventConsumer(db=StubSession(), redis_client=redis_client)
        saved = consumer.consume_store_batch(1)
    finally:
        EventService.ingest_events = original_ingest_events

    assert saved == 1
    assert redis_client.acked