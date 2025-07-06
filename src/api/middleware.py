# Placeholder for FastAPI middleware (auth, logging, etc.) 

import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = getattr(request.state, "correlation_id", None)
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logging.info(
            f"[{correlation_id}] {request.method} {request.url.path} "
            f"completed in {process_time:.2f}ms with status {response.status_code}"
        )
        response.headers["X-Process-Time-ms"] = str(f"{process_time:.2f}")
        return response 