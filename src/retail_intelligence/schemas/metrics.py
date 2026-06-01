from retail_intelligence.schemas.common import APIModel


class StoreMetricsResponse(APIModel):
    store_id: int
    unique_visitors: int
    conversion_rate: float
    avg_dwell_time: float
    queue_depth: int
    abandonment_rate: float
