"""Request/response logging middleware for FastAPI."""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request logging middleware.

    Logs method, path, status code, and latency for every request.
    Attaches a unique request_id to each request for tracing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        request.state.request_id = request_id

        logger.info(
            "→ Request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled exception",
                request_id=request_id,
                error=str(exc),
            )
            raise

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "← Response",
            request_id=request_id,
            status=response.status_code,
            latency_ms=elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
