"""Pydantic models for Glances MCP server configuration."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Environment(str, Enum):
    """Environment types."""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"


class MaintenanceWindow(BaseModel):
    """Maintenance window configuration."""
    name: str
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    days_of_week: list[int] = Field(description="0=Monday, 6=Sunday")
    timezone: str = "UTC"
    suppress_alerts: bool = True


class GlancesServer(BaseModel):
    """Configuration for a Glances server."""
    alias: str
    host: str
    port: int = 61208
    protocol: Literal["http", "https"] = "http"
    username: str | None = None
    password: str | None = None
    environment: Environment | None = None
    region: str | None = None
    tags: list[str] = Field(default_factory=list)
    timeout: int = 30
    enabled: bool = True

    @property
    def base_url(self) -> str:
        """Get the base URL for this server."""
        return f"{self.protocol}://{self.host}:{self.port}"


class AlertThreshold(BaseModel):
    """Alert threshold configuration."""
    metric: str
    warning: float
    critical: float
    unit: str
    comparison: Literal["gt", "lt", "eq"] = "gt"  # greater than, less than, equal
    description: str | None = None


class AlertRule(BaseModel):
    """Alert rule configuration."""
    name: str
    metric_path: str
    thresholds: AlertThreshold
    enabled: bool = True
    server_filter: list[str] | None = None  # server aliases to apply rule to
    environment_filter: list[Environment] | None = None
    tag_filter: list[str] | None = None
    cooldown_minutes: int = 15


class MCPServerConfig(BaseModel):
    """Main MCP server configuration."""
    servers: list[GlancesServer]
    alert_thresholds: list[AlertThreshold] = Field(default_factory=list)
    alert_rules: list[AlertRule] = Field(default_factory=list)
    maintenance_windows: list[MaintenanceWindow] = Field(default_factory=list)
    performance_baseline_retention: int = 7  # days
    alert_history_retention: int = 30  # days

    def get_server_by_alias(self, alias: str) -> GlancesServer | None:
        """Get server by alias."""
        return next((s for s in self.servers if s.alias == alias), None)

    def get_enabled_servers(self) -> list[GlancesServer]:
        """Get all enabled servers."""
        return [s for s in self.servers if s.enabled]

    def get_servers_by_environment(self, env: Environment) -> list[GlancesServer]:
        """Get servers by environment."""
        return [s for s in self.servers if s.environment == env]

    def get_servers_by_tag(self, tag: str) -> list[GlancesServer]:
        """Get servers with specific tag."""
        return [s for s in self.servers if tag in s.tags]


class HealthStatus(BaseModel):
    """Health status for a server or component."""
    status: Literal["healthy", "warning", "critical", "unknown"]
    message: str
    timestamp: datetime
    details: dict[str, Any] | None = None


class ServerStatus(BaseModel):
    """Status information for a Glances server."""
    alias: str
    health: HealthStatus
    last_successful_connection: datetime | None = None
    response_time_ms: float | None = None
    glances_version: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class MetricPoint(BaseModel):
    """A single metric data point."""
    timestamp: datetime
    value: float
    unit: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class TimeSeriesData(BaseModel):
    """Time series data for a metric."""
    metric_name: str
    server_alias: str
    points: list[MetricPoint]
    metadata: dict[str, Any] = Field(default_factory=dict)


class Alert(BaseModel):
    """Alert instance."""
    id: str
    rule_name: str
    server_alias: str
    metric_path: str
    severity: Literal["warning", "critical"]
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_timestamp: datetime | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class PerformanceBaseline(BaseModel):
    """Performance baseline data."""
    server_alias: str
    metric_name: str
    baseline_value: float
    std_deviation: float
    confidence_interval: tuple[float, float]
    sample_size: int
    created_at: datetime
    valid_until: datetime
