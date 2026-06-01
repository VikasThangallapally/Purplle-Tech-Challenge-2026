from sqlalchemy.orm import Session

from retail_intelligence.application.services.anomaly_service import AnomalyService
from retail_intelligence.schemas.analytics import AnomalyResponse


class GetStoreAnomaliesUseCase:
    def __init__(self, db: Session) -> None:
        self._service = AnomalyService.from_session(db)

    def execute(self, store_id: int) -> AnomalyResponse:
        return self._service.detect(store_id)
