from collections.abc import Generator

from redis import Redis

from retail_intelligence.infrastructure.redis.client import get_redis_client
from retail_intelligence.infrastructure.db.session import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> Redis:
    return get_redis_client()
