from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from retail_intelligence.schemas.common import APIModel


class HealthResponse(APIModel):
    status: str
    database: str
    db: str
    redis: str
    last_event_timestamp: str | None = None
    stale_feed: bool = False

class HealthService:
    def __init__(self, db: Session, redis_client: Redis) -> None:
        self._db = db
        self._redis = redis_client

    def get_health(self) -> HealthResponse:
        database_status = self._check_database()
        redis_status = self._check_redis()

        return HealthResponse(
            status="healthy",
            database=database_status,
            db=database_status,
            redis=redis_status,
            last_event_timestamp=None,
            stale_feed=False,
        )

    def _check_database(self) -> str:
        try:
            self._db.execute(text("SELECT 1"))
            return "available"
        except Exception:
            return "unavailable"

    def _check_redis(self) -> str:
        try:
            self._redis.ping()
            return "available"
        except Exception:
            return "unavailable"