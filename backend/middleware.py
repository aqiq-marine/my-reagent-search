import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger("backend.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        response = await call_next(request)

        logger.info(
            "request_id=%s method=%s path=%s status=%s client_ip=%s "
            "x_forwarded_for=%s x_real_ip=%s user_agent=%r referer=%r",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            request.client.host if request.client else "-",
            request.headers.get("x-forwarded-for", "-"),
            request.headers.get("x-real-ip", "-"),
            request.headers.get("user-agent", "-"),
            request.headers.get("referer", "-"),
        )
        response.headers["X-Request-ID"] = request_id
        return response
