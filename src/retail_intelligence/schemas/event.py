from datetime import datetime
from typing import Any

from pydantic import Field

from retail_intelligence.schemas.common import APIModel


class EventIngestItem(APIModel):
    event_id: str
    store_id: int
    camera_id: int | None = None
    visitor_id: str | None = None
    event_type: str
    timestamp: datetime
    zone_id: str | None = None
    dwell_ms: int | None = None
    is_staff: bool = False
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventIngestResponse(APIModel):
    received: int
    saved: int
