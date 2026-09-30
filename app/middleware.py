from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        header_req_id = request.headers.get("x-request-id")
        if header_req_id and header_req_id.strip():
            correlation_id = header_req_id.strip()
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"
        
        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id
        
        start = time.perf_counter()
        response = await call_next(request)
        
        processing_time_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(processing_time_ms)
        
        return response
