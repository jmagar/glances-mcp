"""Pydantic models for Glances MCP server configuration."""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

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
    days_of_week: List[int] = Field(description="0=Monday, 6=Sunday")
    timezone: str = "UTC"
    suppress_alerts: bool = True


class GlancesServer(BaseModel):
    """Configuration for a Glances server."""
    alias: str
    host: str
    port: int = 61208
    protocol: Literal["http", "https"] = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    environment: Optional[Environment] = None
    region: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
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
    description: Optional[str] = None


class AlertRule(BaseModel):
    """Alert rule configuration."""
    name: str
    metric_path: str
    thresholds: AlertThreshold
    enabled: bool = True
    server_filter: Optional[List[str]] = None  # server aliases to apply rule to
    environment_filter: Optional[List[Environment]] = None
    tag_filter: Optional[List[str]] = None
    cooldown_minutes: int = 15


class MCPServerConfig(BaseModel):
    """Main MCP server configuration."""
    servers: List[GlancesServer]
    alert_thresholds: List[AlertThreshold] = Field(default_factory=list)
    alert_rules: List[AlertRule] = Field(default_factory=list)
    maintenance_windows: List[MaintenanceWindow] = Field(default_factory=list)
    performance_baseline_retention: int = 7  # days
    alert_history_retention: int = 30  # days
    
    def get_server_by_alias(self, alias: str) -> Optional[GlancesServer]:
        """Get server by alias."""
        return next((s for s in self.servers if s.alias == alias), None)
    
    def get_enabled_servers(self) -> List[GlancesServer]:
        """Get all enabled servers."""
        return [s for s in self.servers if s.enabled]
    
    def get_servers_by_environment(self, env: Environment) -> List[GlancesServer]:
        """Get servers by environment."""
        return [s for s in self.servers if s.environment == env]
    
    def get_servers_by_tag(self, tag: str) -> List[GlancesServer]:
        """Get servers with specific tag."""
        return [s for s in self.servers if tag in s.tags]


class HealthStatus(BaseModel):
    """Health status for a server or component."""
    status: Literal["healthy", "warning", "critical", "unknown"]
    message: str
    timestamp: datetime
    details: Optional[dict] = None


class ServerStatus(BaseModel):
    """Status information for a Glances server."""
    alias: str
    health: HealthStatus
    last_successful_connection: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    glances_version: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)


class MetricPoint(BaseModel):
    """A single metric data point."""
    timestamp: datetime
    value: float
    unit: Optional[str] = None
    tags: dict = Field(default_factory=dict)


class TimeSeriesData(BaseModel):
    """Time series data for a metric."""
    metric_name: str
    server_alias: str
    points: List[MetricPoint]
    metadata: dict = Field(default_factory=dict)


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
    resolved_timestamp: Optional[datetime] = None
    tags: dict = Field(default_factory=dict)


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