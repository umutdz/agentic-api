import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request.
    The request ID is added to the request headers and response headers.
    """

    async def dispatch(self, request: Request, call_next):
        # Get request ID from headers or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add request ID to request state
        request.state.request_id = request_id

        # Call the next middleware/route handler
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
