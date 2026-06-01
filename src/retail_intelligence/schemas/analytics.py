from pydantic import Field

from retail_intelligence.schemas.common import APIModel


class DropoffPercentages(APIModel):
    entry_to_zone: float = 0.0
    zone_to_queue: float = 0.0
    queue_to_purchase: float = 0.0


class FunnelResponse(APIModel):
    store_id: int
    entry: int = 0
    zone_visit: int = 0
    billing_queue: int = 0
    purchase: int = 0
    dropoff_percentages: DropoffPercentages = Field(default_factory=DropoffPercentages)


class HeatmapZone(APIModel):
    zone_id: str
    visits: int
    avg_dwell: float
    normalized_score: int


class HeatmapResponse(APIModel):
    store_id: int
    zones: list[HeatmapZone]
    data_confidence: str


class AnomalyItem(APIModel):
    type: str
    severity: str
    message: str
    suggested_action: str
    detected_at: str


class AnomalyResponse(APIModel):
    store_id: str
    anomalies: list[AnomalyItem]
