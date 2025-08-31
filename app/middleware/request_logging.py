from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import default_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log incoming requests and responses with request_id tracking.
    This middleware should be added AFTER RequestIDMiddleware to ensure request_id is available.
    """

    async def dispatch(self, request: Request, call_next):
        # Get request_id from request state (set by RequestIDMiddleware) or fallback to header
        request_id = getattr(request.state, "request_id", request.headers.get("X-Request-ID", "unknown"))

        start_time = datetime.now(timezone.utc)

        # Log incoming request
        body = await request.body()

        # Check if the request is multipart/form-data
        content_type = request.headers.get("content-type", "")
        is_multipart = "multipart/form-data" in content_type

        # For multipart requests, don't try to decode the body
        body_str = "{}"
        if not is_multipart and body:
            try:
                body_str = body.decode()
            except UnicodeDecodeError:
                body_str = "<binary content>"

        default_logger.info(
            "Incoming request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            headers=dict(request.headers),
            body=body_str,
            content_type=content_type,
        )

        try:
            response = await call_next(request)

            # Log response
            process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            default_logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time,
            )

            return response
        except Exception as e:
            process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            default_logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=process_time,
            )
            raise
