from sqlalchemy.orm import Session

from retail_intelligence.application.services.anomaly_service import AnomalyService
from retail_intelligence.application.services.funnel_service import FunnelService
from retail_intelligence.application.services.heatmap_service import HeatmapService
from retail_intelligence.application.services.metrics_service import MetricsService
from retail_intelligence.schemas.analytics import AnomalyResponse
from retail_intelligence.schemas.metrics import StoreMetricsResponse


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._metrics_service = MetricsService.from_session(db)
        self._funnel_service = FunnelService.from_session(db)
        self._heatmap_service = HeatmapService.from_session(db)
        self._anomaly_service = AnomalyService.from_session(db)

    def metrics(self, store_id: int) -> StoreMetricsResponse:
        try:
            return self._metrics_service.get_metrics(store_id)
        except Exception:
            return StoreMetricsResponse(
                store_id=store_id,
                unique_visitors=0,
                conversion_rate=0.0,
                avg_dwell_time=0.0,
                queue_depth=0,
                abandonment_rate=0.0,
            )

    def funnel(self, store_id: int):
        return self._funnel_service.get_funnel(store_id)

    def heatmap(self, store_id: int):
        return self._heatmap_service.get_heatmap(store_id)

    def anomalies(self, store_id: int) -> AnomalyResponse:
        return self._anomaly_service.detect(store_id)
