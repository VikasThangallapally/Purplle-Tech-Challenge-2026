from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from retail_intelligence.schemas.event import EventIngestItem


EVENT_STREAM_SUFFIX = "events"
DEAD_LETTER_SUFFIX = "events:dlq"
CONSUMER_GROUP_SUFFIX = "event-consumers"


def store_event_stream_name(store_id: int) -> str:
    return f"store:{store_id}:{EVENT_STREAM_SUFFIX}"


def store_dead_letter_stream_name(store_id: int) -> str:
    return f"store:{store_id}:{DEAD_LETTER_SUFFIX}"


def store_consumer_group_name(store_id: int) -> str:
    return f"store:{store_id}:{CONSUMER_GROUP_SUFFIX}"


@dataclass(slots=True)
class RedisStreamMessage:
    message_id: str
    event: EventIngestItem
    retry_count: int = 0


def encode_event(event: EventIngestItem, retry_count: int = 0) -> dict[str, str]:
    payload = event.model_dump(mode="json")
    payload["metadata"] = json.dumps(payload.get("metadata", {}))
    payload["retry_count"] = str(retry_count)

    encoded: dict[str, str] = {}
    for key, value in payload.items():
        if value is None:
            continue
        encoded[key] = str(value)
    return encoded


def decode_event(message_id: str, payload: dict[str, Any]) -> RedisStreamMessage:
    def _to_int(value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    def _to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def _to_bool(value: Any) -> bool:
        return str(value).lower() in {"1", "true", "yes"}

    timestamp = payload.get("timestamp")
    if isinstance(timestamp, str) and timestamp.endswith("Z"):
        timestamp = timestamp.replace("Z", "+00:00")

    event = EventIngestItem(
        event_id=str(payload["event_id"]),
        store_id=int(payload["store_id"]),
        camera_id=_to_int(payload.get("camera_id")),
        visitor_id=payload.get("visitor_id") or None,
        event_type=str(payload["event_type"]),
        timestamp=datetime.fromisoformat(str(timestamp)),
        zone_id=payload.get("zone_id") or None,
        dwell_ms=_to_int(payload.get("dwell_ms")),
        is_staff=_to_bool(payload.get("is_staff", False)),
        confidence=_to_float(payload.get("confidence")),
        metadata=json.loads(payload.get("metadata", "{}") or "{}"),
    )
    return RedisStreamMessage(message_id=message_id, event=event, retry_count=int(payload.get("retry_count", 0)))
