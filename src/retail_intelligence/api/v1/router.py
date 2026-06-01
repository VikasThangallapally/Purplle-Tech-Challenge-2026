from fastapi import APIRouter

from retail_intelligence.api.v1.endpoints.events import router as events_router
from retail_intelligence.api.v1.endpoints.health import router as health_router
from retail_intelligence.api.v1.endpoints.stores import router as stores_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(events_router)
api_router.include_router(stores_router)
