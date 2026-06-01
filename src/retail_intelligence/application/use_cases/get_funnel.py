from sqlalchemy.orm import Session

from retail_intelligence.application.services.funnel_service import FunnelService
from retail_intelligence.schemas.analytics import FunnelResponse


class GetStoreFunnelUseCase:
    def __init__(self, db: Session) -> None:
        self._service = FunnelService.from_session(db)

    def execute(self, store_id: int) -> FunnelResponse:
        return self._service.get_funnel(store_id)
