"""
Structured logging configuration and middleware.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
from app.config import settings


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "dataset"):
            log_data["dataset"] = record.dataset
        if hasattr(record, "period"):
            log_data["period"] = record.period
        if hasattr(record, "processing_time_ms"):
            log_data["processing_time_ms"] = record.processing_time_ms
        if hasattr(record, "exec_status"):
            log_data["exec_status"] = record.exec_status

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if settings.log_format == "json":
            return json.dumps(log_data)
        else:
            # Human-readable format for development
            return f"[{log_data['timestamp']}] {log_data['level']} - {log_data['message']}"


def setup_logging():
    """Configure application logging."""
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    logging.info(
        f"Logging configured: level={settings.log_level}, format={settings.log_format}"
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with structured data.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        logger = logging.getLogger("sfb.requests")
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Response: {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "processing_time_ms": round(processing_time_ms, 2),
                    "exec_status": "success" if response.status_code < 400 else "error"
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000

            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "processing_time_ms": round(processing_time_ms, 2),
                    "exec_status": "error"
                },
                exc_info=True
            )
            raise
