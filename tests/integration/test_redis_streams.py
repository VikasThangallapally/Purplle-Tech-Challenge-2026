import pytest

pytest.importorskip("redis")

from retail_intelligence.infrastructure.redis.streams import EVENT_STREAM


def test_event_stream_name() -> None:
    assert EVENT_STREAM == "store_events"
