import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        ms = (time.perf_counter() - start) * 1000.0
        rid = getattr(request.state, "request_id", None)
        client_ip = request.headers.get("X-Real-IP") or request.client.host

        # structured fields on the LogRecord
        rec = logging.LogRecord(
            name="access",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        rec.request_id = rid
        rec.path = request.url.path
        rec.method = request.method
        rec.status = response.status_code
        rec.ms = round(ms, 2)
        rec.client_ip = client_ip
        logger.handle(rec)

        return response
