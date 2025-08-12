"""Advanced analytics tools for Glances MCP server."""

from datetime import datetime
from typing import Any

from fastmcp import FastMCP

from glances_mcp.services.baseline_manager import BaselineManager
from glances_mcp.services.glances_client import GlancesClientPool
from glances_mcp.services.health_calculator import HealthCalculator
from glances_mcp.utils.helpers import safe_get
from glances_mcp.utils.logging import logger, performance_logger
from glances_mcp.utils.metrics import MetricsCalculator


def register_advanced_analytics_tools(
    app: FastMCP,
    client_pool: GlancesClientPool,
    baseline_manager: BaselineManager
) -> None:
    """Register advanced analytics tools with the MCP server."""

    health_calculator = HealthCalculator()
    metrics_calculator = MetricsCalculator()

    @app.tool()
    async def generate_health_score(
        server_alias: str | None = None,
        weights: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Generate comprehensive health scores for servers."""
        start_time = datetime.now()

        try:
            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()

            health_scores = {}

            for alias, client in clients.items():
                try:
                    health_data = await health_calculator.calculate_server_health(
                        client, weights
                    )
                    health_scores[alias] = health_data

                except Exception as e:
                    logger.warning(
                        "Error calculating health score for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    health_scores[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "overall_score": 0.0,
                        "status": "error",
                        "timestamp": datetime.now().isoformat()
                    }

            # Calculate fleet-wide summary
            fleet_summary = _calculate_fleet_health_summary(health_scores)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("generate_health_score", duration_ms, True)

            return {
                "servers": health_scores,
                "fleet_summary": fleet_summary
            }

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("generate_health_score", duration_ms, False)
            logger.error("Error in generate_health_score", server_alias=server_alias, error=str(e))
            raise

    @app.tool()
    async def performance_comparison(
        server_alias: str | None = None,
        baseline_hours: int = 24,
        metrics: list[str] | None = None
    ) -> dict[str, Any]:
        """Compare current performance against historical baselines."""
        start_time = datetime.now()

        try:
            if metrics is None:
                metrics = ["cpu.total", "mem.percent", "load.min5"]

            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()

            comparison_results = {}

            for alias, client in clients.items():
                try:
                    # Get current metrics
                    current_metrics = {}
                    cpu_data = await client.get_cpu_info()
                    memory_data = await client.get_memory_info()
                    load_data = await client.get_load_average()

                    current_metrics.update({
                        "cpu.total": safe_get(cpu_data, "total", 0),
                        "mem.percent": safe_get(memory_data, "percent", 0),
                        "load.min1": safe_get(load_data, "min1", 0),
                        "load.min5": safe_get(load_data, "min5", 0),
                        "load.min15": safe_get(load_data, "min15", 0)
                    })

                    # Compare against baselines
                    metric_comparisons = {}
                    overall_status = "normal"
                    deviations = []

                    for metric in metrics:
                        if metric in current_metrics:
                            current_value = current_metrics[metric]

                            # Get baseline comparison
                            comparison = baseline_manager.compare_to_baseline(
                                alias, metric, current_value
                            )

                            if comparison:
                                metric_comparisons[metric] = comparison

                                # Track overall status
                                if comparison["status"] == "critical":
                                    overall_status = "critical"
                                elif comparison["status"] == "warning" and overall_status != "critical":
                                    overall_status = "warning"

                                # Track significant deviations
                                if abs(comparison["z_score"]) > 1.5:
                                    deviations.append({
                                        "metric": metric,
                                        "z_score": comparison["z_score"],
                                        "percent_change": comparison["percent_change"],
                                        "status": comparison["status"]
                                    })
                            else:
                                metric_comparisons[metric] = {
                                    "status": "no_baseline",
                                    "current_value": current_value,
                                    "message": "No baseline available for comparison"
                                }

                    # Get trend analysis
                    trend_analysis = {}
                    for metric in metrics:
                        trend = baseline_manager.get_trend_analysis(alias, metric)
                        if trend:
                            trend_analysis[metric] = trend

                    comparison_result = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "current_metrics": current_metrics,
                        "baseline_comparison": metric_comparisons,
                        "trend_analysis": trend_analysis,
                        "overall_status": overall_status,
                        "significant_deviations": deviations,
                        "summary": {
                            "metrics_compared": len(metric_comparisons),
                            "metrics_with_baselines": len([
                                comp for comp in metric_comparisons.values()
                                if comp.get("status") != "no_baseline"
                            ]),
                            "critical_metrics": len([
                                comp for comp in metric_comparisons.values()
                                if comp.get("status") == "critical"
                            ]),
                            "warning_metrics": len([
                                comp for comp in metric_comparisons.values()
                                if comp.get("status") == "warning"
                            ])
                        }
                    }

                    comparison_results[alias] = comparison_result

                except Exception as e:
                    logger.warning(
                        "Error in performance comparison for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    comparison_results[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("performance_comparison", duration_ms, True)

            return {"servers": comparison_results}

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("performance_comparison", duration_ms, False)
            logger.error("Error in performance_comparison", server_alias=server_alias, error=str(e))
            raise

    @app.tool()
    async def detect_anomalies(
        server_alias: str | None = None,
        threshold_std: float = 2.0,
        window_hours: int = 6
    ) -> dict[str, Any]:
        """Detect statistical anomalies in server metrics."""
        start_time = datetime.now()

        try:
            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()

            anomaly_results = {}

            for alias, client in clients.items():
                try:
                    # Get recent data for anomaly detection
                    anomalies_found = []

                    # Check key metrics for anomalies
                    metrics_to_check = ["cpu.total", "mem.percent", "load.min5"]

                    for metric in metrics_to_check:
                        # Get historical data from baseline manager
                        buffer = baseline_manager._get_server_data_buffer(alias, metric)
                        all_points = buffer.get_all()

                        if len(all_points) > 10:  # Need sufficient data
                            values = [p.value for p in all_points if hasattr(p, "value")]

                            # Detect anomalies
                            anomalies = metrics_calculator.detect_anomalies(
                                values, threshold_std
                            )

                            for idx, value, anomaly_type in anomalies:
                                # Only report recent anomalies (last few samples)
                                if idx >= len(values) - 5:
                                    anomalies_found.append({
                                        "metric": metric,
                                        "value": value,
                                        "type": anomaly_type,
                                        "index": idx,
                                        "severity": "critical" if abs(values[idx] - sum(values)/len(values)) > threshold_std * 2 else "warning"
                                    })

                    # Get current metrics for context
                    current_metrics = {}
                    try:
                        cpu_data = await client.get_cpu_info()
                        memory_data = await client.get_memory_info()
                        load_data = await client.get_load_average()

                        current_metrics.update({
                            "cpu.total": safe_get(cpu_data, "total", 0),
                            "mem.percent": safe_get(memory_data, "percent", 0),
                            "load.min5": safe_get(load_data, "min5", 0)
                        })
                    except Exception:
                        pass

                    anomaly_result = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "anomalies": anomalies_found,
                        "current_metrics": current_metrics,
                        "detection_params": {
                            "threshold_std": threshold_std,
                            "window_hours": window_hours,
                            "metrics_checked": metrics_to_check
                        },
                        "summary": {
                            "total_anomalies": len(anomalies_found),
                            "critical_anomalies": len([
                                a for a in anomalies_found
                                if a["severity"] == "critical"
                            ]),
                            "warning_anomalies": len([
                                a for a in anomalies_found
                                if a["severity"] == "warning"
                            ]),
                            "has_recent_anomalies": len(anomalies_found) > 0
                        }
                    }

                    anomaly_results[alias] = anomaly_result

                except Exception as e:
                    logger.warning(
                        "Error detecting anomalies for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    anomaly_results[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "anomalies": [],
                        "summary": {"total_anomalies": 0, "has_recent_anomalies": False}
                    }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("detect_anomalies", duration_ms, True)

            return {"servers": anomaly_results}

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("detect_anomalies", duration_ms, False)
            logger.error("Error in detect_anomalies", server_alias=server_alias, error=str(e))
            raise

    @app.tool()
    async def capacity_analysis(
        server_alias: str | None = None,
        projection_days: int = 30
    ) -> dict[str, Any]:
        """Analyze current capacity utilization and project future needs."""
        start_time = datetime.now()

        try:
            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()

            capacity_results = {}

            for alias, client in clients.items():
                try:
                    # Get current utilization
                    cpu_data = await client.get_cpu_info()
                    memory_data = await client.get_memory_info()
                    disk_data = await client.get_disk_usage()
                    load_data = await client.get_load_average()
                    system_data = await client.get_system_info()

                    # Calculate current capacity utilization
                    cpu_utilization = safe_get(cpu_data, "total", 0)
                    memory_utilization = safe_get(memory_data, "percent", 0)

                    # Find highest disk utilization
                    disk_utilizations = [safe_get(disk, "percent", 0) for disk in disk_data]
                    max_disk_utilization = max(disk_utilizations) if disk_utilizations else 0

                    # Load utilization (normalized by CPU count)
                    cpu_count = safe_get(system_data, "cpucount", 1)
                    load_5min = safe_get(load_data, "min5", 0)
                    load_utilization = min((load_5min / cpu_count) * 100, 200)  # Cap at 200%

                    # Get trend data for projections
                    cpu_trend = baseline_manager.get_trend_analysis(alias, "cpu.total", 24 * 7)  # 1 week
                    memory_trend = baseline_manager.get_trend_analysis(alias, "mem.percent", 24 * 7)

                    # Simple linear projection
                    projections = {}

                    if cpu_trend and cpu_trend["direction"] == "increasing":
                        days_to_80 = _calculate_days_to_threshold(
                            cpu_utilization, 80, cpu_trend["recent_change"], projection_days
                        )
                        days_to_90 = _calculate_days_to_threshold(
                            cpu_utilization, 90, cpu_trend["recent_change"], projection_days
                        )
                        projections["cpu"] = {
                            "current": cpu_utilization,
                            "trend_direction": cpu_trend["direction"],
                            "recent_change_percent": cpu_trend["recent_change"],
                            "days_to_80_percent": days_to_80,
                            "days_to_90_percent": days_to_90
                        }

                    if memory_trend and memory_trend["direction"] == "increasing":
                        days_to_80 = _calculate_days_to_threshold(
                            memory_utilization, 80, memory_trend["recent_change"], projection_days
                        )
                        days_to_90 = _calculate_days_to_threshold(
                            memory_utilization, 90, memory_trend["recent_change"], projection_days
                        )
                        projections["memory"] = {
                            "current": memory_utilization,
                            "trend_direction": memory_trend["direction"],
                            "recent_change_percent": memory_trend["recent_change"],
                            "days_to_80_percent": days_to_80,
                            "days_to_90_percent": days_to_90
                        }

                    # Capacity recommendations
                    recommendations = []
                    risk_level = "low"

                    if cpu_utilization > 80:
                        recommendations.append("CPU utilization is high - consider CPU upgrade")
                        risk_level = "high"
                    elif cpu_utilization > 60:
                        recommendations.append("CPU utilization is elevated - monitor closely")
                        if risk_level == "low":
                            risk_level = "medium"

                    if memory_utilization > 85:
                        recommendations.append("Memory utilization is high - consider RAM upgrade")
                        risk_level = "high"
                    elif memory_utilization > 70:
                        recommendations.append("Memory utilization is elevated - monitor closely")
                        if risk_level == "low":
                            risk_level = "medium"

                    if max_disk_utilization > 90:
                        recommendations.append("Disk space is critically low - immediate action required")
                        risk_level = "high"
                    elif max_disk_utilization > 80:
                        recommendations.append("Disk space is running low - plan for expansion")
                        if risk_level == "low":
                            risk_level = "medium"

                    if load_utilization > 150:
                        recommendations.append("System load is very high - performance may be degraded")
                        risk_level = "high"

                    capacity_result = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "current_utilization": {
                            "cpu_percent": cpu_utilization,
                            "memory_percent": memory_utilization,
                            "disk_max_percent": max_disk_utilization,
                            "load_normalized_percent": load_utilization
                        },
                        "projections": projections,
                        "risk_assessment": {
                            "level": risk_level,
                            "recommendations": recommendations,
                            "immediate_action_required": risk_level == "high"
                        },
                        "resource_details": {
                            "cpu_count": cpu_count,
                            "total_memory_gb": safe_get(memory_data, "total", 0) / (1024**3),
                            "disk_count": len(disk_data),
                            "highest_disk_usage": {
                                "percent": max_disk_utilization,
                                "mount_point": next(
                                    (disk["mnt_point"] for disk in disk_data
                                     if safe_get(disk, "percent", 0) == max_disk_utilization),
                                    "unknown"
                                ) if disk_data else "unknown"
                            }
                        }
                    }

                    capacity_results[alias] = capacity_result

                except Exception as e:
                    logger.warning(
                        "Error in capacity analysis for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    capacity_results[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "risk_assessment": {"level": "unknown"}
                    }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("capacity_analysis", duration_ms, True)

            return {"servers": capacity_results}

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("capacity_analysis", duration_ms, False)
            logger.error("Error in capacity_analysis", server_alias=server_alias, error=str(e))
            raise


def _calculate_fleet_health_summary(health_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Calculate fleet-wide health summary."""
    if not health_scores:
        return {"total_servers": 0}

    total_servers = len(health_scores)
    healthy_servers = len([s for s in health_scores.values() if s.get("status") == "healthy"])
    warning_servers = len([s for s in health_scores.values() if s.get("status") == "warning"])
    critical_servers = len([s for s in health_scores.values() if s.get("status") == "critical"])
    error_servers = len([s for s in health_scores.values() if s.get("status") == "error"])

    # Calculate average score
    valid_scores = [s["overall_score"] for s in health_scores.values() if isinstance(s.get("overall_score"), int | float)]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    # Determine fleet status
    if critical_servers > 0 or error_servers > 0:
        fleet_status = "critical"
    elif warning_servers > total_servers * 0.3:  # More than 30% have warnings
        fleet_status = "warning"
    elif healthy_servers >= total_servers * 0.8:  # 80% or more are healthy
        fleet_status = "healthy"
    else:
        fleet_status = "degraded"

    return {
        "total_servers": total_servers,
        "healthy_servers": healthy_servers,
        "warning_servers": warning_servers,
        "critical_servers": critical_servers,
        "error_servers": error_servers,
        "fleet_status": fleet_status,
        "average_score": round(avg_score, 2),
        "health_percentage": round((healthy_servers / total_servers) * 100, 1) if total_servers > 0 else 0
    }


def _calculate_days_to_threshold(
    current_value: float,
    threshold: float,
    daily_change_percent: float,
    max_days: int
) -> int | None:
    """Calculate days until a metric reaches a threshold based on trend."""
    if daily_change_percent <= 0 or current_value >= threshold:
        return None

    # Convert weekly change to daily change
    daily_change = daily_change_percent / 7

    if daily_change == 0:
        return None

    # Calculate days to reach threshold
    days_needed = (threshold - current_value) / (current_value * daily_change / 100)

    return int(days_needed) if 0 < days_needed <= max_days else None
