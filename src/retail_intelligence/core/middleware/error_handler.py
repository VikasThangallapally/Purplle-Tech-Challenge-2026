import logging
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Unhandled request error")
            return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})
