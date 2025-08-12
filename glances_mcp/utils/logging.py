"""Structured logging configuration for Glances MCP server."""

from datetime import datetime
import logging
import sys
import types
from typing import Any, cast

import structlog
from structlog.typing import FilteringBoundLogger

from glances_mcp.config.settings import settings


def configure_logging() -> FilteringBoundLogger:
    """Configure structured logging for the application."""

    # Configure structlog
    renderer: structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer
    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.set_exc_info,
            structlog.processors.StackInfoRenderer(),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout if not settings.log_file else None,
        filename=settings.log_file,
        level=getattr(logging, settings.log_level.upper()),
    )

    return cast(FilteringBoundLogger, structlog.get_logger())


class RequestLogger:
    """Request logging context manager."""

    def __init__(self, logger: FilteringBoundLogger, request_id: str):
        self.logger = logger
        self.request_id = request_id
        self.start_time = datetime.now()

    def __enter__(self) -> FilteringBoundLogger:
        """Enter context with request logging."""
        self.bound_logger = self.logger.bind(
            request_id=self.request_id,
            start_time=self.start_time.isoformat()
        )
        self.bound_logger.info("Request started")
        return self.bound_logger

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        """Exit context with request logging."""
        end_time = datetime.now()
        duration_ms = (end_time - self.start_time).total_seconds() * 1000

        if exc_type:
            self.bound_logger.error(
                "Request failed",
                end_time=end_time.isoformat(),
                duration_ms=duration_ms,
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )
        else:
            self.bound_logger.info(
                "Request completed",
                end_time=end_time.isoformat(),
                duration_ms=duration_ms
            )


class PerformanceLogger:
    """Performance logging utilities."""

    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger

    def log_operation_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Log performance metrics for an operation."""
        log_data = {
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            log_data.update(metadata)

        if success:
            self.logger.info("Operation completed", **log_data)
        else:
            self.logger.warning("Operation failed", **log_data)

    def log_server_response_time(
        self,
        server_alias: str,
        endpoint: str,
        response_time_ms: float,
        success: bool = True
    ) -> None:
        """Log server response time metrics."""
        self.log_operation_performance(
            operation="glances_api_call",
            duration_ms=response_time_ms,
            success=success,
            metadata={
                "server_alias": server_alias,
                "endpoint": endpoint
            }
        )

    def log_tool_execution(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool = True,
        parameters: dict[str, Any] | None = None
    ) -> None:
        """Log tool execution metrics."""
        metadata: dict[str, Any] = {"tool_name": tool_name}
        if parameters:
            metadata["parameters"] = parameters

        self.log_operation_performance(
            operation="tool_execution",
            duration_ms=duration_ms,
            success=success,
            metadata=metadata
        )


# Global logger instances
logger = configure_logging()
performance_logger = PerformanceLogger(logger)
