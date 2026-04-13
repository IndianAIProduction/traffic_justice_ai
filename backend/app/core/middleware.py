import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms}ms)"
        )

        response.headers["X-Request-ID"] = request_id
        return response
