"""Input validation utilities for Glances MCP server."""

import re
from typing import Any

from pydantic import BaseModel, ValidationError

from .models import AlertThreshold, GlancesServer


class ServerValidationMixin:
    """Validation methods for server configurations."""

    @staticmethod
    def validate_server_alias(alias: str) -> str:
        """Validate server alias format."""
        if not alias:
            raise ValueError("Server alias cannot be empty")

        if len(alias) > 64:
            raise ValueError("Server alias must be 64 characters or less")

        # Allow alphanumeric, dashes, underscores, and spaces
        if not re.match(r"^[a-zA-Z0-9\-_\s]+$", alias):
            raise ValueError("Server alias can only contain alphanumeric characters, dashes, underscores, and spaces")

        return alias.strip()

    @staticmethod
    def validate_host(host: str) -> str:
        """Validate host format (IP or hostname)."""
        if not host:
            raise ValueError("Host cannot be empty")

        # Basic validation - more comprehensive validation could use ipaddress module
        if not re.match(r"^[a-zA-Z0-9\.\-]+$", host):
            raise ValueError("Invalid host format")

        return host.strip()

    @staticmethod
    def validate_port(port: int) -> int:
        """Validate port number."""
        if not isinstance(port, int):
            raise ValueError("Port must be an integer")

        if port < 1 or port > 65535:
            raise ValueError("Port must be between 1 and 65535")

        return port


class MetricValidationMixin:
    """Validation methods for metrics and thresholds."""

    @staticmethod
    def validate_metric_name(metric: str) -> str:
        """Validate metric name format."""
        if not metric:
            raise ValueError("Metric name cannot be empty")

        # Allow alphanumeric, dots, dashes, underscores
        if not re.match(r"^[a-zA-Z0-9\.\-_]+$", metric):
            raise ValueError("Metric name can only contain alphanumeric characters, dots, dashes, and underscores")

        return metric.strip()

    @staticmethod
    def validate_threshold_values(warning: float, critical: float, comparison: str = "gt") -> None:
        """Validate threshold values are logical."""
        if comparison == "gt":
            if warning >= critical:
                raise ValueError("For 'greater than' thresholds, warning must be less than critical")
        elif comparison == "lt":
            if warning <= critical:
                raise ValueError("For 'less than' thresholds, warning must be greater than critical")


class InputValidator(BaseModel, ServerValidationMixin, MetricValidationMixin):
    """Main input validator class."""

    @classmethod
    def validate_server_config(cls, server_data: dict[str, Any]) -> GlancesServer:
        """Validate and create a server configuration."""
        try:
            # Pre-validate specific fields
            if "alias" in server_data:
                server_data["alias"] = cls.validate_server_alias(server_data["alias"])

            if "host" in server_data:
                server_data["host"] = cls.validate_host(server_data["host"])

            if "port" in server_data:
                server_data["port"] = cls.validate_port(server_data["port"])

            return GlancesServer.model_validate(server_data)

        except ValidationError as e:
            raise ValueError(f"Server configuration validation failed: {e}") from e

    @classmethod
    def validate_alert_threshold(cls, threshold_data: dict[str, Any]) -> AlertThreshold:
        """Validate and create an alert threshold."""
        try:
            # Pre-validate metric name
            if "metric" in threshold_data:
                threshold_data["metric"] = cls.validate_metric_name(threshold_data["metric"])

            threshold = AlertThreshold.model_validate(threshold_data)

            # Validate threshold logic
            cls.validate_threshold_values(
                threshold.warning,
                threshold.critical,
                threshold.comparison
            )

            return threshold

        except ValidationError as e:
            raise ValueError(f"Alert threshold validation failed: {e}") from e

    @classmethod
    def validate_tool_params(cls, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Validate tool parameters."""
        validated_params = {}

        # Common parameter validation
        if "server_alias" in params:
            if params["server_alias"] and not isinstance(params["server_alias"], str):
                raise ValueError("server_alias must be a string")
            validated_params["server_alias"] = params.get("server_alias")

        if "limit" in params:
            limit = params.get("limit", 10)
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                raise ValueError("limit must be an integer between 1 and 1000")
            validated_params["limit"] = limit

        if "sort_by" in params:
            sort_by = params.get("sort_by", "cpu")
            if sort_by not in ["cpu", "memory", "name", "pid"]:
                raise ValueError("sort_by must be one of: cpu, memory, name, pid")
            validated_params["sort_by"] = sort_by

        # Tool-specific validation
        if tool_name == "get_top_processes":
            validated_params.update(cls._validate_process_params(params))
        elif tool_name == "get_containers":
            validated_params.update(cls._validate_container_params(params))
        elif tool_name == "check_alert_conditions":
            validated_params.update(cls._validate_alert_params(params))

        return validated_params

    @classmethod
    def _validate_process_params(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Validate process-related parameters."""
        validated = {}

        if "filter_name" in params:
            filter_name = params.get("filter_name")
            if filter_name and not isinstance(filter_name, str):
                raise ValueError("filter_name must be a string")
            validated["filter_name"] = filter_name

        return validated

    @classmethod
    def _validate_container_params(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Validate container-related parameters."""
        validated = {}

        if "include_stopped" in params:
            include_stopped = params.get("include_stopped", False)
            if not isinstance(include_stopped, bool):
                raise ValueError("include_stopped must be a boolean")
            validated["include_stopped"] = include_stopped

        return validated

    @classmethod
    def _validate_alert_params(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Validate alert-related parameters."""
        validated = {}

        if "severity" in params:
            severity = params.get("severity")
            if severity and severity not in ["warning", "critical"]:
                raise ValueError("severity must be 'warning' or 'critical'")
            validated["severity"] = severity

        return validated
