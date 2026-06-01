from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ZoneLastActivity:
    zone_id: str
    last_seen_at: datetime