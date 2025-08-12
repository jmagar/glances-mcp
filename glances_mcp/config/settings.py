"""Settings management for Glances MCP server."""

import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import MCPServerConfig


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GLANCES_MCP_",
        case_sensitive=False
    )

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False

    # Glances configuration
    glances_timeout: int = 30
    glances_retry_attempts: int = 3
    glances_retry_delay: int = 5

    # Performance configuration
    baseline_retention_days: int = 7
    alert_history_retention_days: int = 30
    max_concurrent_requests: int = 100

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str | None = None

    # Configuration file path
    config_file: str = "config/config.json"

    # Health check configuration
    health_check_interval: int = 60  # seconds
    health_check_timeout: int = 10  # seconds

    # MCP configuration
    mcp_server_name: str = "glances-mcp-server"
    mcp_server_version: str = "1.0.0"

    def load_mcp_config(self) -> MCPServerConfig:
        """Load MCP server configuration from file."""
        config_path = Path(self.config_file)

        if not config_path.exists():
            # Return default configuration if file doesn't exist
            return MCPServerConfig(servers=[])

        try:
            with open(config_path) as f:
                config_data = json.load(f)
            return MCPServerConfig.model_validate(config_data)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}") from e

    def save_mcp_config(self, config: MCPServerConfig) -> None:
        """Save MCP server configuration to file."""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, "w") as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {config_path}: {e}") from e


# Global settings instance
settings = Settings()
