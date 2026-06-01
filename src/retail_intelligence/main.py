from fastapi import FastAPI

from retail_intelligence.api.v1.router import api_router
from retail_intelligence.core.config import settings
from retail_intelligence.core.exceptions import register_exception_handlers
from retail_intelligence.core.logging import configure_logging
from retail_intelligence.core.middleware.error_handler import ErrorHandlerMiddleware
from retail_intelligence.core.middleware.request_id import RequestIdMiddleware
from retail_intelligence.core.middleware.timing import TimingMiddleware


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
