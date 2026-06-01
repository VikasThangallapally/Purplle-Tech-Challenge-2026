from retail_intelligence.core.config import settings
from retail_intelligence.infrastructure.db.session import SessionLocal
from retail_intelligence.infrastructure.redis.event_consumer import EventConsumer


def _parse_store_ids() -> list[int]:
    if not settings.redis_stream_store_ids.strip():
        return []
    return [int(value.strip()) for value in settings.redis_stream_store_ids.split(",") if value.strip()]


def run() -> None:
    store_ids = _parse_store_ids()
    if not store_ids:
        return

    db = SessionLocal()
    try:
        consumer = EventConsumer(db=db)
        consumer.consume_forever(store_ids)
    finally:
        db.close()
