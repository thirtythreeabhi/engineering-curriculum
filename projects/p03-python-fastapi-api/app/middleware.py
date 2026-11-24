"""Custom request tracing and latency middleware."""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Extract existing trace ID or generate a new UUIDv4
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # 2. Record start timestamp
        start_time = time.perf_counter()

        # 3. Process the request through the stack
        response = await call_next(request)

        # 4. Compute latency in milliseconds
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # 5. Attach diagnostic tracing headers to the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        return response
