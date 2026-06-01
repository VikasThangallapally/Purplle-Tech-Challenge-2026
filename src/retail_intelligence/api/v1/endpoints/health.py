from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy.orm import Session

from retail_intelligence.api.deps import get_db, get_redis
from retail_intelligence.application.services.health_service import HealthResponse, HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)) -> HealthResponse:
    return HealthService(db=db, redis_client=redis_client).get_health()
