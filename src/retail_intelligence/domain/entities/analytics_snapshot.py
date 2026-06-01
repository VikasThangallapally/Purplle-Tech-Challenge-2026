from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AnalyticsSnapshot:
    store_id: int
    generated_at: datetime
    metrics: dict[str, Any] = field(default_factory=dict)
