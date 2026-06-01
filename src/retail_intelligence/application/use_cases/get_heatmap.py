from sqlalchemy.orm import Session

from retail_intelligence.application.services.heatmap_service import HeatmapService
from retail_intelligence.schemas.analytics import HeatmapResponse


class GetStoreHeatmapUseCase:
    def __init__(self, db: Session) -> None:
        self._service = HeatmapService.from_session(db)

    def execute(self, store_id: int) -> HeatmapResponse:
        return self._service.get_heatmap(store_id)
