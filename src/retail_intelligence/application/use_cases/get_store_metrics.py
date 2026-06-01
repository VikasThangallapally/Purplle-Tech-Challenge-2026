from sqlalchemy.orm import Session

from retail_intelligence.application.services.metrics_service import MetricsService
from retail_intelligence.schemas.metrics import StoreMetricsResponse


class GetStoreMetricsUseCase:
    def __init__(self, db: Session) -> None:
        self._service = MetricsService.from_session(db)

    def execute(self, store_id: int) -> StoreMetricsResponse:
        return self._service.get_metrics(store_id)
