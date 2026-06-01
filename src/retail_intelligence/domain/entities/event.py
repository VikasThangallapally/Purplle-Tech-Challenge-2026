from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Event:
    event_id: str
    store_id: int
    camera_id: int | None
    visitor_id: str | None
    event_type: str
    timestamp: datetime
    zone_id: str | None
    dwell_ms: int | None
    is_staff: bool
    confidence: float | None
    metadata: dict[str, Any] = field(default_factory=dict)
