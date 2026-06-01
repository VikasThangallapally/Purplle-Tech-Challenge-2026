from retail_intelligence.core.config import settings
from retail_intelligence.infrastructure.redis.redis_stream import (
	CONSUMER_GROUP_SUFFIX,
	DEAD_LETTER_SUFFIX,
	EVENT_STREAM_SUFFIX,
	store_consumer_group_name,
	store_dead_letter_stream_name,
	store_event_stream_name,
)


EVENT_STREAM = settings.redis_stream_events

__all__ = [
	"CONSUMER_GROUP_SUFFIX",
	"DEAD_LETTER_SUFFIX",
	"EVENT_STREAM_SUFFIX",
	"EVENT_STREAM",
	"store_consumer_group_name",
	"store_dead_letter_stream_name",
	"store_event_stream_name",
]
