from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from redis import Redis
from redis.exceptions import ResponseError

from retail_intelligence.application.services.event_service import EventService
from retail_intelligence.infrastructure.db.repositories.event_repository_impl import EventRepositoryImpl
from retail_intelligence.infrastructure.redis.client import get_redis_client
from retail_intelligence.infrastructure.redis.redis_stream import (
    RedisStreamMessage,
    decode_event,
    encode_event,
    store_consumer_group_name,
    store_dead_letter_stream_name,
    store_event_stream_name,
)

logger = logging.getLogger(__name__)


class EventConsumer:
    def __init__(
        self,
        db,
        redis_client: Redis | None = None,
        consumer_name: str = "retail-stream-consumer",
        batch_size: int = 100,
        block_ms: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 0.2,
    ) -> None:
        self._redis = redis_client or get_redis_client()
        self._consumer_name = consumer_name
        self._batch_size = batch_size
        self._block_ms = block_ms
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._event_service = EventService(EventRepositoryImpl(db))

    def consume_store_batch(self, store_id: int) -> int:
        stream_name = store_event_stream_name(store_id)
        group_name = store_consumer_group_name(store_id)
        self._ensure_group(stream_name, group_name)

        try:
            messages = self._redis.xreadgroup(
                groupname=group_name,
                consumername=self._consumer_name,
                streams={stream_name: ">"},
                count=self._batch_size,
                block=self._block_ms,
            )
        except Exception:
            logger.exception("Failed to read Redis stream batch", extra={"store_id": store_id, "stream_name": stream_name})
            return 0

        if not messages:
            return 0

        batch = self._decode_messages(messages)
        if not batch:
            return 0

        try:
            result = self._event_service.ingest_events([message.event for message in batch])
            self._ack_messages(stream_name, group_name, batch)
            logger.info(
                "Consumed Redis Stream batch",
                extra={"store_id": store_id, "stream_name": stream_name, "received": result.received, "saved": result.saved},
            )
            return result.saved
        except Exception:
            logger.exception("Failed to process Redis stream batch", extra={"store_id": store_id, "stream_name": stream_name, "batch_size": len(batch)})
            self._retry_or_dead_letter(store_id, stream_name, group_name, batch)
            return 0

    def consume_forever(self, store_ids: Sequence[int]) -> None:
        while True:
            processed = 0
            for store_id in store_ids:
                processed += self.consume_store_batch(store_id)
            if processed == 0:
                time.sleep(self._retry_delay)

    def _ensure_group(self, stream_name: str, group_name: str) -> None:
        try:
            self._redis.xgroup_create(stream_name, group_name, id="0-0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def _decode_messages(self, messages) -> list[RedisStreamMessage]:
        batch: list[RedisStreamMessage] = []
        for _, payloads in messages:
            for message_id, payload in payloads:
                batch.append(decode_event(message_id, payload))
        return batch

    def _ack_messages(self, stream_name: str, group_name: str, batch: Sequence[RedisStreamMessage]) -> None:
        message_ids = [message.message_id for message in batch]
        if message_ids:
            self._redis.xack(stream_name, group_name, *message_ids)

    def _retry_or_dead_letter(self, store_id: int, stream_name: str, group_name: str, batch: Sequence[RedisStreamMessage]) -> None:
        dead_letter_stream = store_dead_letter_stream_name(store_id)
        for message in batch:
            next_retry_count = message.retry_count + 1
            if next_retry_count < self._max_retries:
                logger.info(
                    "Requeueing Redis stream message",
                    extra={"store_id": store_id, "stream_name": stream_name, "event_id": message.event.event_id, "retry_count": next_retry_count},
                )
                self._redis.xadd(stream_name, encode_event(message.event, retry_count=next_retry_count))
            else:
                logger.warning(
                    "Sending Redis stream message to dead letter stream",
                    extra={"store_id": store_id, "stream_name": stream_name, "event_id": message.event.event_id, "retry_count": next_retry_count},
                )
                dead_letter_payload = encode_event(message.event, retry_count=next_retry_count)
                dead_letter_payload["error_type"] = "processing_failure"
                self._redis.xadd(dead_letter_stream, dead_letter_payload)

        self._ack_messages(stream_name, group_name, batch)
