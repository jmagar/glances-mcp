"""Configuration resources for Glances MCP server."""

import json
from typing import Any, cast

from fastmcp import FastMCP

from glances_mcp.config.settings import settings
from glances_mcp.services.glances_client import GlancesClientPool


def register_configuration_resources(app: FastMCP, client_pool: GlancesClientPool) -> None:
    """Register configuration resources with the MCP server."""

    @app.resource("glances://config/servers")
    async def servers_config() -> str:
        """Complete server inventory with configuration metadata and connection parameters."""
        try:
            mcp_config = settings.load_mcp_config()

            servers_info: list[dict[str, Any]] = []
            for server in mcp_config.servers:
                # Get current status if available
                server_status = None
                client = client_pool.get_client(server.alias)
                if client:
                    try:
                        status = await client.health_check()
                        server_status = {
                            "health": status.health.status,
                            "last_check": status.health.timestamp.isoformat(),
                            "response_time_ms": status.response_time_ms,
                            "glances_version": status.glances_version,
                            "capabilities": status.capabilities
                        }
                    except Exception:
                        server_status = {"health": "unknown", "error": "Unable to get status"}

                server_info = {
                    "alias": server.alias,
                    "connection": {
                        "host": server.host,
                        "port": server.port,
                        "protocol": server.protocol,
                        "base_url": server.base_url,
                        "timeout": server.timeout,
                        "has_auth": bool(server.username and server.password)
                    },
                    "classification": {
                        "environment": server.environment.value if server.environment else None,
                        "region": server.region,
                        "tags": server.tags
                    },
                    "status": server_status,
                    "enabled": server.enabled,
                    "configuration_metadata": {
                        "created": "Configuration creation time not tracked",
                        "last_modified": "Configuration modification time not tracked",
                        "config_version": "1.0"
                    }
                }

                servers_info.append(server_info)

            # Server summary statistics
            total_servers = len(servers_info)
            enabled_servers = len([s for s in servers_info if s["enabled"]])

            # Extract environments safely with type casting
            environments = list({
                cast(dict[str, Any], s["classification"])["environment"]
                for s in servers_info
                if cast(dict[str, Any], s["classification"])["environment"] is not None
            })

            # Extract regions safely with type casting
            regions = list({
                cast(dict[str, Any], s["classification"])["region"]
                for s in servers_info
                if cast(dict[str, Any], s["classification"])["region"] is not None
            })

            # Extract tags safely
            all_tags: set[str] = set()
            for server_dict in servers_info:
                server_classification = cast(dict[str, Any], server_dict["classification"])
                server_tags = cast(list[str], server_classification["tags"])
                all_tags.update(server_tags)

            config_resource = {
                "resource_info": {
                    "uri": "glances://config/servers",
                    "name": "Server Configuration Inventory",
                    "description": "Complete inventory of all configured Glances servers with metadata",
                    "type": "configuration",
                    "last_updated": "Real-time",
                    "format": "JSON"
                },
                "summary": {
                    "total_servers": total_servers,
                    "enabled_servers": enabled_servers,
                    "disabled_servers": total_servers - enabled_servers,
                    "environments": environments,
                    "regions": regions,
                    "unique_tags": sorted(all_tags),
                    "protocols": list({
                        cast(dict[str, Any], s["connection"])["protocol"]
                        for s in servers_info
                    })
                },
                "servers": servers_info,
                "configuration_guidelines": {
                    "server_naming": "Use descriptive aliases that include environment and purpose",
                    "environment_classification": "Always specify environment (production, staging, development)",
                    "tagging_strategy": "Use consistent tags for grouping and filtering (e.g., 'web', 'database', 'cache')",
                    "security": "Use authentication for production servers, consider HTTPS for sensitive environments"
                }
            }

            return json.dumps(config_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://config/servers",
                    "name": "Server Configuration Inventory",
                    "error": str(e)
                },
                "servers": [],
                "message": "Unable to load server configuration"
            }
            return json.dumps(error_response, indent=2)

    @app.resource("glances://config/thresholds")
    async def thresholds_config() -> str:
        """Alert threshold configurations with templates and modification history."""
        try:
            mcp_config = settings.load_mcp_config()

            # Process alert thresholds
            thresholds_info = []
            for threshold in mcp_config.alert_thresholds:
                threshold_info = {
                    "metric": threshold.metric,
                    "thresholds": {
                        "warning": threshold.warning,
                        "critical": threshold.critical,
                        "unit": threshold.unit,
                        "comparison": threshold.comparison
                    },
                    "description": threshold.description,
                    "configuration": {
                        "created": "Threshold creation time not tracked",
                        "last_modified": "Threshold modification time not tracked"
                    }
                }
                thresholds_info.append(threshold_info)

            # Process alert rules
            rules_info: list[dict[str, Any]] = []
            for rule in mcp_config.alert_rules:
                rule_info = {
                    "name": rule.name,
                    "metric_path": rule.metric_path,
                    "thresholds": {
                        "warning": rule.thresholds.warning,
                        "critical": rule.thresholds.critical,
                        "unit": rule.thresholds.unit,
                        "comparison": rule.thresholds.comparison
                    },
                    "filters": {
                        "servers": rule.server_filter,
                        "environments": [env.value for env in rule.environment_filter] if rule.environment_filter else None,
                        "tags": rule.tag_filter
                    },
                    "settings": {
                        "enabled": rule.enabled,
                        "cooldown_minutes": rule.cooldown_minutes
                    }
                }
                rules_info.append(rule_info)

            # Default threshold templates
            default_templates = {
                "cpu_thresholds": {
                    "cpu.total": {"warning": 80.0, "critical": 90.0, "unit": "%", "comparison": "gt"},
                    "cpu.iowait": {"warning": 20.0, "critical": 40.0, "unit": "%", "comparison": "gt"},
                    "cpu.steal": {"warning": 10.0, "critical": 20.0, "unit": "%", "comparison": "gt"}
                },
                "memory_thresholds": {
                    "mem.percent": {"warning": 85.0, "critical": 95.0, "unit": "%", "comparison": "gt"},
                    "mem.available": {"warning": 1073741824, "critical": 536870912, "unit": "bytes", "comparison": "lt"}  # 1GB/512MB
                },
                "disk_thresholds": {
                    "disk.percent": {"warning": 85.0, "critical": 95.0, "unit": "%", "comparison": "gt"},
                    "disk.free": {"warning": 5368709120, "critical": 1073741824, "unit": "bytes", "comparison": "lt"}  # 5GB/1GB
                },
                "load_thresholds": {
                    "load.min5": {"warning": 2.0, "critical": 4.0, "unit": "load", "comparison": "gt"},
                    "load.min15": {"warning": 1.5, "critical": 3.0, "unit": "load", "comparison": "gt"}
                },
                "network_thresholds": {
                    "network.error_rate": {"warning": 0.1, "critical": 1.0, "unit": "%", "comparison": "gt"}
                }
            }

            thresholds_resource = {
                "resource_info": {
                    "uri": "glances://config/thresholds",
                    "name": "Alert Threshold Configuration",
                    "description": "Alert threshold configurations, rules, and templates",
                    "type": "configuration",
                    "last_updated": "Real-time",
                    "format": "JSON"
                },
                "summary": {
                    "total_thresholds": len(thresholds_info),
                    "total_rules": len(rules_info),
                    "enabled_rules": len([
                        r for r in rules_info
                        if cast(dict[str, Any], r["settings"])["enabled"]
                    ]),
                    "metrics_monitored": list({t["metric"] for t in thresholds_info})
                },
                "current_thresholds": thresholds_info,
                "alert_rules": rules_info,
                "threshold_templates": default_templates,
                "configuration_guidelines": {
                    "threshold_setting": "Set warning thresholds 10-15% below critical to allow response time",
                    "metric_paths": "Use dot notation for nested metrics (e.g., 'cpu.total', 'mem.percent')",
                    "comparison_operators": "Use 'gt' for utilization metrics, 'lt' for availability metrics",
                    "cooldown_periods": "Set appropriate cooldown to prevent alert spam (typically 15-60 minutes)"
                },
                "best_practices": {
                    "cpu_thresholds": "Consider workload patterns - batch jobs may have higher acceptable peaks",
                    "memory_thresholds": "Account for buffer/cache usage in memory threshold calculations",
                    "disk_thresholds": "Set different thresholds for different mount points based on criticality",
                    "load_thresholds": "Normalize by CPU count for meaningful load average thresholds"
                }
            }

            return json.dumps(thresholds_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://config/thresholds",
                    "name": "Alert Threshold Configuration",
                    "error": str(e)
                },
                "current_thresholds": [],
                "alert_rules": [],
                "message": "Unable to load threshold configuration"
            }
            return json.dumps(error_response, indent=2)

    @app.resource("glances://config/maintenance_windows")
    async def maintenance_windows_config() -> str:
        """Maintenance window configurations and schedules."""
        try:
            mcp_config = settings.load_mcp_config()

            maintenance_windows: list[dict[str, Any]] = []
            for window in mcp_config.maintenance_windows:
                window_info = {
                    "name": window.name,
                    "schedule": {
                        "start_time": window.start_time,
                        "end_time": window.end_time,
                        "days_of_week": window.days_of_week,
                        "timezone": window.timezone
                    },
                    "settings": {
                        "suppress_alerts": window.suppress_alerts
                    },
                    "day_names": [
                        "Monday", "Tuesday", "Wednesday", "Thursday",
                        "Friday", "Saturday", "Sunday"
                    ]
                }

                # Add human-readable day names
                day_names: list[str] = []
                window_day_names = cast(list[str], window_info["day_names"])
                for day_num in window.days_of_week:
                    day_names.append(window_day_names[day_num])
                window_info["readable_schedule"] = {
                    "days": day_names,
                    "time": f"{window.start_time} - {window.end_time} ({window.timezone})"
                }

                maintenance_windows.append(window_info)

            # Sample maintenance window templates
            sample_templates = {
                "weekly_maintenance": {
                    "name": "Weekly Maintenance",
                    "start_time": "02:00",
                    "end_time": "06:00",
                    "days_of_week": [6],  # Sunday
                    "timezone": "UTC",
                    "suppress_alerts": True
                },
                "business_hours": {
                    "name": "Business Hours",
                    "start_time": "08:00",
                    "end_time": "18:00",
                    "days_of_week": [0, 1, 2, 3, 4],  # Monday-Friday
                    "timezone": "America/New_York",
                    "suppress_alerts": False
                },
                "emergency_maintenance": {
                    "name": "Emergency Maintenance",
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "days_of_week": [0, 1, 2, 3, 4, 5, 6],  # All days
                    "timezone": "UTC",
                    "suppress_alerts": True
                }
            }

            maintenance_resource = {
                "resource_info": {
                    "uri": "glances://config/maintenance_windows",
                    "name": "Maintenance Window Configuration",
                    "description": "Scheduled maintenance windows and alert suppression settings",
                    "type": "configuration",
                    "last_updated": "Real-time",
                    "format": "JSON"
                },
                "summary": {
                    "total_windows": len(maintenance_windows),
                    "windows_with_suppression": len([
                        w for w in maintenance_windows
                        if cast(dict[str, Any], w["settings"])["suppress_alerts"]
                    ]),
                    "timezones_used": list({
                        cast(dict[str, Any], w["schedule"])["timezone"]
                        for w in maintenance_windows
                    }) if maintenance_windows else []
                },
                "maintenance_windows": maintenance_windows,
                "templates": sample_templates,
                "configuration_guidelines": {
                    "scheduling": "Schedule maintenance during low-traffic periods",
                    "alert_suppression": "Enable alert suppression for planned maintenance to reduce noise",
                    "timezone_consistency": "Use UTC for global infrastructure, local timezone for regional systems",
                    "window_duration": "Keep maintenance windows as short as practical to minimize impact"
                },
                "day_of_week_mapping": {
                    "0": "Monday",
                    "1": "Tuesday",
                    "2": "Wednesday",
                    "3": "Thursday",
                    "4": "Friday",
                    "5": "Saturday",
                    "6": "Sunday"
                }
            }

            return json.dumps(maintenance_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://config/maintenance_windows",
                    "name": "Maintenance Window Configuration",
                    "error": str(e)
                },
                "maintenance_windows": [],
                "message": "Unable to load maintenance window configuration"
            }
            return json.dumps(error_response, indent=2)

    @app.resource("glances://config/settings")
    async def application_settings() -> str:
        """Application settings and configuration parameters."""
        try:
            # Get current application settings (filtered for security)
            app_settings = {
                "server": {
                    "host": settings.host,
                    "port": settings.port,
                    "debug": settings.debug,
                    "mcp_server_name": settings.mcp_server_name,
                    "mcp_server_version": settings.mcp_server_version
                },
                "glances_client": {
                    "timeout": settings.glances_timeout,
                    "retry_attempts": settings.glances_retry_attempts,
                    "retry_delay": settings.glances_retry_delay
                },
                "performance": {
                    "max_concurrent_requests": settings.max_concurrent_requests,
                    "baseline_retention_days": settings.baseline_retention_days,
                    "alert_history_retention_days": settings.alert_history_retention_days
                },
                "logging": {
                    "log_level": settings.log_level,
                    "log_format": settings.log_format,
                    "log_file": settings.log_file
                },
                "health_checks": {
                    "health_check_interval": settings.health_check_interval,
                    "health_check_timeout": settings.health_check_timeout
                }
            }

            # Configuration file information
            config_info = {
                "config_file_path": settings.config_file,
                "environment_variables_prefix": "GLANCES_MCP_",
                "configuration_sources": ["Environment Variables", "Configuration File", "Defaults"]
            }

            # Default configuration template
            default_config = {
                "servers": [
                    {
                        "alias": "example-server",
                        "host": "localhost",
                        "port": 61208,
                        "protocol": "http",
                        "username": None,
                        "password": None,
                        "environment": "development",
                        "region": "local",
                        "tags": ["example", "test"],
                        "timeout": 30,
                        "enabled": True
                    }
                ],
                "alert_thresholds": [
                    {
                        "metric": "cpu.total",
                        "warning": 80.0,
                        "critical": 90.0,
                        "unit": "%",
                        "comparison": "gt",
                        "description": "Total CPU utilization"
                    }
                ],
                "alert_rules": [
                    {
                        "name": "high_cpu_usage",
                        "metric_path": "cpu.total",
                        "thresholds": {
                            "metric": "cpu.total",
                            "warning": 80.0,
                            "critical": 90.0,
                            "unit": "%",
                            "comparison": "gt"
                        },
                        "enabled": True,
                        "cooldown_minutes": 15
                    }
                ],
                "maintenance_windows": [],
                "performance_baseline_retention": 7,
                "alert_history_retention": 30
            }

            settings_resource = {
                "resource_info": {
                    "uri": "glances://config/settings",
                    "name": "Application Settings",
                    "description": "Current application configuration and settings",
                    "type": "configuration",
                    "last_updated": "Real-time",
                    "format": "JSON"
                },
                "current_settings": app_settings,
                "configuration_info": config_info,
                "default_configuration_template": default_config,
                "environment_variables": {
                    "GLANCES_MCP_HOST": "Server host address",
                    "GLANCES_MCP_PORT": "Server port number",
                    "GLANCES_MCP_DEBUG": "Enable debug mode (true/false)",
                    "GLANCES_MCP_LOG_LEVEL": "Logging level (DEBUG, INFO, WARNING, ERROR)",
                    "GLANCES_MCP_LOG_FORMAT": "Log format (json, text)",
                    "GLANCES_MCP_CONFIG_FILE": "Path to configuration file",
                    "GLANCES_MCP_GLANCES_TIMEOUT": "Glances API timeout in seconds",
                    "GLANCES_MCP_MAX_CONCURRENT_REQUESTS": "Maximum concurrent requests"
                },
                "configuration_validation": {
                    "server_ports": "Must be between 1 and 65535",
                    "timeout_values": "Must be positive integers",
                    "retention_days": "Must be positive integers",
                    "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "log_formats": ["json", "text"]
                }
            }

            return json.dumps(settings_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://config/settings",
                    "name": "Application Settings",
                    "error": str(e)
                },
                "current_settings": {},
                "message": "Unable to load application settings"
            }
            return json.dumps(error_response, indent=2)
