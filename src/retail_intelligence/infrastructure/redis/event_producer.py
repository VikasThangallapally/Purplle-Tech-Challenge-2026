from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Sequence

from redis import Redis

from retail_intelligence.infrastructure.redis.client import get_redis_client
from retail_intelligence.infrastructure.redis.redis_stream import encode_event, store_event_stream_name
from retail_intelligence.schemas.event import EventIngestItem

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self, redis_client: Redis | None = None, max_retries: int = 3, retry_delay: float = 0.2) -> None:
        self._redis = redis_client or get_redis_client()
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def publish_event(self, event: EventIngestItem) -> str:
        return self.publish_events([event])[0]

    def publish_events(self, events: Sequence[EventIngestItem]) -> list[str]:
        if not events:
            return []

        grouped: dict[int, list[EventIngestItem]] = defaultdict(list)
        for event in events:
            grouped[event.store_id].append(event)

        published_ids: list[str] = []
        for store_id, store_events in grouped.items():
            published_ids.extend(self._publish_store_batch(store_id, store_events))
        return published_ids

    def _publish_store_batch(self, store_id: int, events: Sequence[EventIngestItem]) -> list[str]:
        stream_name = store_event_stream_name(store_id)
        attempt = 0
        while True:
            try:
                logger.info("Publishing events to Redis Stream", extra={"store_id": store_id, "stream_name": stream_name, "batch_size": len(events)})
                published_ids = []
                for event in events:
                    published_id = self._redis.xadd(stream_name, encode_event(event))
                    published_ids.append(str(published_id))
                return published_ids
            except Exception:
                attempt += 1
                logger.exception("Failed to publish Redis stream batch", extra={"store_id": store_id, "stream_name": stream_name, "attempt": attempt})
                if attempt >= self._max_retries:
                    raise
                time.sleep(self._retry_delay * attempt)
