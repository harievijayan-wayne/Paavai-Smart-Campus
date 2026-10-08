import logging
import sys
import time
import uuid
from typing import Any, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Sensitive field scrubbing set
SENSITIVE_FIELDS = {
    "password", "secret", "token", "access_token", "jwt", "authorization",
    "cookie", "set-cookie", "refresh_token", "hash"
}


def sanitize_payload(data: Any) -> Any:
    """Recursively removes sensitive keys from dict payloads prior to logging."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_FIELDS:
                cleaned[k] = "******"
            elif isinstance(v, (dict, list)):
                cleaned[k] = sanitize_payload(v)
            else:
                cleaned[k] = v
        return cleaned
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data


def setup_logging():
    """Initializes structured logger for Paavai Smart Campus AI."""
    logger = logging.getLogger("smartcampus")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [REQ:%(request_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.addFilter(LoggingContextFilter("SYSTEM"))

    # Silence overly verbose external loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)

    return logger


class LoggingContextFilter(logging.Filter):
    """Injects dynamic request_id into log records."""
    def __init__(self, request_id: str = "SYS"):
        super().__init__()
        self.request_id = request_id

    def filter(self, record):
        record.request_id = getattr(record, "request_id", self.request_id)
        return True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for measuring API request latency and logging error states."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        logger = logging.getLogger("smartcampus")
        log_filter = LoggingContextFilter(request_id)
        logger.addFilter(log_filter)

        start_time = time.perf_counter()
        try:
            response: Response = await call_next(request)
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            response.headers["X-Request-ID"] = request_id

            if request.url.path not in ["/health", "/docs", "/openapi.json"]:
                logger.info(
                    f"{request.method} {request.url.path} -> {response.status_code} in {process_time_ms}ms"
                )
            return response
        except Exception as exc:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled API Error on {request.method} {request.url.path} after {process_time_ms}ms: {str(exc)}",
                exc_info=True
            )
            raise exc
        finally:
            logger.removeFilter(log_filter)


logger = setup_logging()
LoggingMiddleware = RequestLoggingMiddleware
