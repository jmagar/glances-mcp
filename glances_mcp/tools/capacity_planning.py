"""Capacity planning tools for Glances MCP server."""

from datetime import datetime, timedelta
from typing import Any

from fastmcp import FastMCP

from glances_mcp.services.baseline_manager import BaselineManager
from glances_mcp.services.glances_client import GlancesClientPool
from glances_mcp.utils.helpers import safe_get
from glances_mcp.utils.logging import logger, performance_logger


def register_capacity_planning_tools(
    app: FastMCP,
    client_pool: GlancesClientPool,
    baseline_manager: BaselineManager
) -> None:
    """Register capacity planning tools with the MCP server."""

    @app.tool()
    async def predict_resource_needs(
        server_alias: str | None = None,
        projection_days: int = 90,
        confidence_level: float = 0.80
    ) -> dict[str, Any]:
        """Predict future resource needs based on historical trends and growth patterns."""
        start_time = datetime.now()

        try:
            if projection_days < 1 or projection_days > 365:
                raise ValueError("projection_days must be between 1 and 365")

            if confidence_level < 0.5 or confidence_level > 0.99:
                raise ValueError("confidence_level must be between 0.5 and 0.99")

            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()

            predictions = {}

            for alias, client in clients.items():
                try:
                    # Get current resource utilization
                    cpu_data = await client.get_cpu_info()
                    memory_data = await client.get_memory_info()
                    disk_data = await client.get_disk_usage()
                    load_data = await client.get_load_average()
                    system_data = await client.get_system_info()

                    current_utilization = {
                        "cpu_percent": safe_get(cpu_data, "total", 0),
                        "memory_percent": safe_get(memory_data, "percent", 0),
                        "memory_total_gb": safe_get(memory_data, "total", 0) / (1024**3),
                        "memory_used_gb": safe_get(memory_data, "used", 0) / (1024**3),
                        "load_avg": safe_get(load_data, "min5", 0),
                        "cpu_count": safe_get(system_data, "cpucount", 1)
                    }

                    # Get trend analysis for prediction
                    cpu_trend = baseline_manager.get_trend_analysis(alias, "cpu.total", 24 * 7)  # 1 week
                    memory_trend = baseline_manager.get_trend_analysis(alias, "mem.percent", 24 * 7)
                    load_trend = baseline_manager.get_trend_analysis(alias, "load.min5", 24 * 7)

                    # Calculate predictions
                    resource_predictions = {}

                    # CPU prediction
                    if cpu_trend and cpu_trend["confidence"] >= confidence_level:
                        cpu_prediction = _predict_resource_growth(
                            current_utilization["cpu_percent"],
                            cpu_trend["recent_change"],
                            projection_days,
                            "cpu_percent"
                        )
                        cpu_prediction["trend_confidence"] = cpu_trend["confidence"]
                        resource_predictions["cpu"] = cpu_prediction

                    # Memory prediction
                    if memory_trend and memory_trend["confidence"] >= confidence_level:
                        memory_prediction = _predict_resource_growth(
                            current_utilization["memory_percent"],
                            memory_trend["recent_change"],
                            projection_days,
                            "memory_percent"
                        )
                        memory_prediction["trend_confidence"] = memory_trend["confidence"]

                        # Calculate absolute memory predictions
                        current_memory_gb = current_utilization["memory_used_gb"]
                        total_memory_gb = current_utilization["memory_total_gb"]

                        predicted_memory_percent = memory_prediction["predicted_value"]
                        predicted_memory_gb = (predicted_memory_percent / 100) * total_memory_gb

                        memory_prediction["predicted_memory_gb"] = predicted_memory_gb
                        memory_prediction["memory_growth_gb"] = predicted_memory_gb - current_memory_gb
                        memory_prediction["total_memory_gb"] = total_memory_gb

                        resource_predictions["memory"] = memory_prediction

                    # Load prediction
                    if load_trend and load_trend["confidence"] >= confidence_level:
                        load_prediction = _predict_resource_growth(
                            current_utilization["load_avg"],
                            load_trend["recent_change"],
                            projection_days,
                            "load_average"
                        )
                        load_prediction["trend_confidence"] = load_trend["confidence"]
                        load_prediction["cpu_count"] = current_utilization["cpu_count"]
                        load_prediction["normalized_current"] = current_utilization["load_avg"] / current_utilization["cpu_count"]
                        load_prediction["normalized_predicted"] = load_prediction["predicted_value"] / current_utilization["cpu_count"]

                        resource_predictions["load"] = load_prediction

                    # Disk space prediction (for major filesystems)
                    disk_predictions = []
                    for disk in disk_data:
                        if safe_get(disk, "mnt_point") in ["/", "/home", "/var", "/opt"]:
                            disk_usage_percent = safe_get(disk, "percent", 0)

                            # Simple linear projection based on current growth
                            # This is a basic approximation - real world would use more sophisticated models
                            if disk_usage_percent > 10:  # Only predict if there's meaningful usage
                                # Assume 1% growth per month as baseline (adjustable)
                                monthly_growth = 1.0
                                predicted_usage = disk_usage_percent + (monthly_growth * projection_days / 30)

                                disk_prediction = {
                                    "mount_point": safe_get(disk, "mnt_point"),
                                    "current_usage_percent": disk_usage_percent,
                                    "predicted_usage_percent": min(predicted_usage, 100),
                                    "size_gb": safe_get(disk, "size", 0) / (1024**3),
                                    "free_gb": safe_get(disk, "free", 0) / (1024**3),
                                    "growth_rate_monthly": monthly_growth,
                                    "days_to_90_percent": _calculate_days_to_threshold(
                                        disk_usage_percent, 90, monthly_growth / 30
                                    ) if disk_usage_percent < 90 else None,
                                    "days_to_95_percent": _calculate_days_to_threshold(
                                        disk_usage_percent, 95, monthly_growth / 30
                                    ) if disk_usage_percent < 95 else None
                                }
                                disk_predictions.append(disk_prediction)

                    # Generate capacity recommendations
                    recommendations = _generate_capacity_recommendations(
                        current_utilization, resource_predictions, disk_predictions, projection_days
                    )

                    # Calculate resource adequacy scores
                    adequacy_scores = _calculate_resource_adequacy(
                        resource_predictions, projection_days
                    )

                    prediction_result = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "projection_parameters": {
                            "projection_days": projection_days,
                            "confidence_level": confidence_level,
                            "end_date": (datetime.now() + timedelta(days=projection_days)).isoformat()[:10]
                        },
                        "current_utilization": current_utilization,
                        "resource_predictions": resource_predictions,
                        "disk_predictions": disk_predictions,
                        "adequacy_scores": adequacy_scores,
                        "recommendations": recommendations,
                        "summary": {
                            "overall_risk_level": _assess_overall_capacity_risk(adequacy_scores),
                            "resources_at_risk": len([r for r in adequacy_scores.values() if r.get("risk_level") in ["high", "critical"]]),
                            "immediate_action_needed": any(
                                r.get("risk_level") == "critical" for r in adequacy_scores.values()
                            ),
                            "planning_horizon_days": projection_days
                        }
                    }

                    predictions[alias] = prediction_result

                except Exception as e:
                    logger.warning(
                        "Error predicting resource needs for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    predictions[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("predict_resource_needs", duration_ms, True)

            return {"servers": predictions}

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("predict_resource_needs", duration_ms, False)
            logger.error("Error in predict_resource_needs", server_alias=server_alias, error=str(e))
            raise

    @app.tool()
    async def compare_servers(
        server_aliases: list[str] | None = None,
        metrics: list[str] | None = None
    ) -> dict[str, Any]:
        """Compare resource utilization and performance across servers."""
        start_time = datetime.now()

        try:
            if metrics is None:
                metrics = ["cpu_usage", "memory_usage", "load_average", "disk_usage"]

            clients = {}
            if server_aliases:
                for alias in server_aliases:
                    if alias not in client_pool.servers:
                        raise ValueError(f"Server '{alias}' not found")
                    client = client_pool.get_client(alias)
                    if client:
                        clients[alias] = client
            else:
                clients = client_pool.get_enabled_clients()

            if len(clients) < 2:
                return {
                    "error": "At least 2 servers required for comparison",
                    "available_servers": list(clients.keys())
                }

            server_data = {}

            # Collect metrics from all servers
            for alias, client in clients.items():
                try:
                    cpu_data = await client.get_cpu_info()
                    memory_data = await client.get_memory_info()
                    disk_data = await client.get_disk_usage()
                    load_data = await client.get_load_average()
                    system_data = await client.get_system_info()

                    # Calculate aggregate disk usage
                    disk_usages = [safe_get(disk, "percent", 0) for disk in disk_data]
                    avg_disk_usage = sum(disk_usages) / len(disk_usages) if disk_usages else 0
                    max_disk_usage = max(disk_usages) if disk_usages else 0

                    server_metrics = {
                        "cpu_usage": safe_get(cpu_data, "total", 0),
                        "memory_usage": safe_get(memory_data, "percent", 0),
                        "load_average": safe_get(load_data, "min5", 0),
                        "disk_usage_avg": avg_disk_usage,
                        "disk_usage_max": max_disk_usage,
                        "cpu_count": safe_get(system_data, "cpucount", 1),
                        "memory_total_gb": safe_get(memory_data, "total", 0) / (1024**3),
                        "load_normalized": safe_get(load_data, "min5", 0) / safe_get(system_data, "cpucount", 1),
                        "server_config": client_pool.servers[alias]
                    }

                    server_data[alias] = server_metrics

                except Exception as e:
                    logger.warning(
                        "Error collecting metrics for server comparison",
                        server_alias=alias,
                        error=str(e)
                    )
                    server_data[alias] = {"error": str(e)}

            # Perform comparisons
            # comparison_results: dict[str, Any] = {}

            # Statistical analysis of each metric
            metric_stats = {}
            for metric in metrics:
                if metric == "disk_usage":
                    values = [data["disk_usage_max"] for data in server_data.values() if "error" not in data]
                else:
                    values = [data.get(metric, 0) for data in server_data.values() if "error" not in data]

                if values:
                    metric_stats[metric] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "range": max(values) - min(values),
                        "std_dev": _calculate_std_dev(values)
                    }

            # Identify outliers and leaders
            outliers = {}
            leaders = {}

            for metric in metrics:
                if metric in metric_stats:
                    stats = metric_stats[metric]
                    threshold = stats["avg"] + (2 * stats["std_dev"])  # 2 sigma

                    # High outliers (concerning for most metrics)
                    high_outliers = [
                        alias for alias, data in server_data.items()
                        if "error" not in data and data.get(metric == "disk_usage" and "disk_usage_max" or metric, 0) > threshold
                    ]

                    # Leaders (best performers)
                    best_performers = sorted(
                        [(alias, data) for alias, data in server_data.items() if "error" not in data],
                        key=lambda x: x[1].get(metric == "disk_usage" and "disk_usage_max" or metric, 0)
                    )[:3]

                    if high_outliers:
                        outliers[metric] = high_outliers

                    leaders[metric] = [alias for alias, _ in best_performers]

            # Resource efficiency analysis
            efficiency_scores = {}
            for alias, data in server_data.items():
                if "error" not in data:
                    # Simple efficiency score (lower is better for utilization metrics)
                    cpu_score = 100 - data["cpu_usage"]
                    memory_score = 100 - data["memory_usage"]
                    load_score = max(0, 100 - (data["load_normalized"] * 100))
                    disk_score = 100 - data["disk_usage_max"]

                    efficiency_scores[alias] = {
                        "cpu_efficiency": cpu_score,
                        "memory_efficiency": memory_score,
                        "load_efficiency": load_score,
                        "disk_efficiency": disk_score,
                        "overall_efficiency": (cpu_score + memory_score + load_score + disk_score) / 4
                    }

            # Environment and tag analysis
            environment_analysis = _analyze_by_environment(server_data, client_pool)
            tag_analysis = _analyze_by_tags(server_data, client_pool)

            comparison_result = {
                "timestamp": datetime.now().isoformat(),
                "servers_compared": len([s for s in server_data.values() if "error" not in s]),
                "servers_with_errors": len([s for s in server_data.values() if "error" in s]),
                "metrics_analyzed": metrics,
                "server_data": server_data,
                "statistical_analysis": metric_stats,
                "performance_leaders": leaders,
                "outliers": outliers,
                "efficiency_scores": efficiency_scores,
                "environment_analysis": environment_analysis,
                "tag_analysis": tag_analysis,
                "recommendations": _generate_comparison_recommendations(
                    server_data, outliers, leaders, efficiency_scores
                )
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("compare_servers", duration_ms, True)

            return comparison_result

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("compare_servers", duration_ms, False)
            logger.error("Error in compare_servers", server_aliases=server_aliases, error=str(e))
            raise


def _predict_resource_growth(
    current_value: float,
    recent_change_percent: float,
    projection_days: int,
    resource_type: str
) -> dict[str, Any]:
    """Predict resource growth using linear trend."""
    # Convert weekly change to daily change
    daily_change_percent = recent_change_percent / 7

    # Project future value
    projected_change = daily_change_percent * projection_days
    predicted_value = current_value + (current_value * projected_change / 100)

    # Apply reasonable bounds
    if resource_type in ["cpu_percent", "memory_percent"]:
        predicted_value = max(0, min(predicted_value, 100))
    elif resource_type == "load_average":
        predicted_value = max(0, predicted_value)

    return {
        "current_value": current_value,
        "predicted_value": predicted_value,
        "growth_amount": predicted_value - current_value,
        "growth_percent": ((predicted_value - current_value) / current_value * 100) if current_value > 0 else 0,
        "daily_change_percent": daily_change_percent,
        "projection_days": projection_days
    }


def _calculate_days_to_threshold(current: float, threshold: float, daily_change: float) -> int | None:
    """Calculate days to reach threshold."""
    if daily_change <= 0 or current >= threshold:
        return None

    days = (threshold - current) / daily_change
    return int(days) if days > 0 else None


def _generate_capacity_recommendations(
    current: dict[str, Any],
    predictions: dict[str, dict[str, Any]],
    disk_predictions: list[dict[str, Any]],
    projection_days: int
) -> list[str]:
    """Generate capacity planning recommendations."""
    recommendations = []

    # CPU recommendations
    if "cpu" in predictions:
        cpu_pred = predictions["cpu"]
        if cpu_pred["predicted_value"] > 90:
            recommendations.append(
                f"Critical: CPU utilization predicted to reach {cpu_pred['predicted_value']:.1f}% "
                f"in {projection_days} days. Plan CPU upgrade immediately."
            )
        elif cpu_pred["predicted_value"] > 80:
            recommendations.append(
                f"Warning: CPU utilization predicted to reach {cpu_pred['predicted_value']:.1f}% "
                f"in {projection_days} days. Consider CPU upgrade planning."
            )

    # Memory recommendations
    if "memory" in predictions:
        mem_pred = predictions["memory"]
        if mem_pred["predicted_value"] > 90:
            additional_gb = mem_pred["memory_growth_gb"]
            recommendations.append(
                f"Critical: Memory utilization predicted to reach {mem_pred['predicted_value']:.1f}% "
                f"({additional_gb:.1f} GB additional) in {projection_days} days. Plan memory upgrade."
            )
        elif mem_pred["predicted_value"] > 80:
            recommendations.append(
                f"Warning: Memory utilization predicted to reach {mem_pred['predicted_value']:.1f}% "
                f"in {projection_days} days. Monitor closely and plan for potential upgrade."
            )

    # Load recommendations
    if "load" in predictions:
        load_pred = predictions["load"]
        if load_pred["normalized_predicted"] > 2.0:
            recommendations.append(
                f"Critical: System load predicted to reach {load_pred['predicted_value']:.1f} "
                f"({load_pred['normalized_predicted']:.1f} per CPU) in {projection_days} days. "
                "Performance will be severely impacted."
            )
        elif load_pred["normalized_predicted"] > 1.5:
            recommendations.append(
                f"Warning: System load predicted to reach {load_pred['predicted_value']:.1f} "
                f"in {projection_days} days. Monitor for performance impact."
            )

    # Disk recommendations
    for disk_pred in disk_predictions:
        if disk_pred.get("days_to_95_percent") and disk_pred["days_to_95_percent"] <= projection_days:
            recommendations.append(
                f"Critical: {disk_pred['mount_point']} predicted to reach 95% capacity "
                f"in {disk_pred['days_to_95_percent']} days. Plan disk expansion immediately."
            )
        elif disk_pred.get("days_to_90_percent") and disk_pred["days_to_90_percent"] <= projection_days:
            recommendations.append(
                f"Warning: {disk_pred['mount_point']} predicted to reach 90% capacity "
                f"in {disk_pred['days_to_90_percent']} days. Plan disk expansion."
            )

    if not recommendations:
        recommendations.append("No immediate capacity concerns identified for the projection period.")

    return recommendations


def _calculate_resource_adequacy(predictions: dict[str, dict[str, Any]], projection_days: int) -> dict[str, Any]:
    """Calculate adequacy scores for predicted resource utilization."""
    adequacy_scores = {}

    for resource, pred in predictions.items():
        predicted_value = pred["predicted_value"]

        if resource in ["cpu", "memory"]:
            if predicted_value >= 95:
                risk_level = "critical"
                adequacy_score = 0
            elif predicted_value >= 85:
                risk_level = "high"
                adequacy_score = 25
            elif predicted_value >= 70:
                risk_level = "medium"
                adequacy_score = 50
            elif predicted_value >= 50:
                risk_level = "low"
                adequacy_score = 75
            else:
                risk_level = "minimal"
                adequacy_score = 100

        elif resource == "load":
            normalized = predicted_value / pred.get("cpu_count", 1)
            if normalized >= 3.0:
                risk_level = "critical"
                adequacy_score = 0
            elif normalized >= 2.0:
                risk_level = "high"
                adequacy_score = 25
            elif normalized >= 1.5:
                risk_level = "medium"
                adequacy_score = 50
            elif normalized >= 1.0:
                risk_level = "low"
                adequacy_score = 75
            else:
                risk_level = "minimal"
                adequacy_score = 100
        else:
            # Default scoring for other resources
            risk_level = "unknown"
            adequacy_score = 50

        adequacy_scores[resource] = {
            "adequacy_score": adequacy_score,
            "risk_level": risk_level,
            "predicted_value": predicted_value,
            "projection_days": projection_days
        }

    return adequacy_scores


def _assess_overall_capacity_risk(adequacy_scores: dict[str, Any]) -> str:
    """Assess overall capacity risk level."""
    if not adequacy_scores:
        return "unknown"

    risk_levels = [score["risk_level"] for score in adequacy_scores.values()]

    if "critical" in risk_levels:
        return "critical"
    elif "high" in risk_levels:
        return "high"
    elif "medium" in risk_levels:
        return "medium"
    elif "low" in risk_levels:
        return "low"
    else:
        return "minimal"


def _calculate_std_dev(values: list[float]) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return float(variance ** 0.5)


def _analyze_by_environment(server_data: dict[str, Any], client_pool: GlancesClientPool) -> dict[str, Any]:
    """Analyze server performance by environment."""
    env_analysis: dict[str, dict[str, Any]] = {}

    for alias, data in server_data.items():
        if "error" in data:
            continue

        server_config = client_pool.servers.get(alias)
        if not server_config or not server_config.environment:
            continue

        env = server_config.environment.value
        if env not in env_analysis:
            env_analysis[env] = {
                "servers": [],
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
                "avg_load": 0.0
            }

        env_data = env_analysis[env]
        env_data["servers"].append(alias)
        env_data["avg_cpu"] += data.get("cpu_usage", 0)
        env_data["avg_memory"] += data.get("memory_usage", 0)
        env_data["avg_load"] += data.get("load_normalized", 0)

    # Calculate averages
    for _env, data in env_analysis.items():
        server_count = len(data["servers"])
        if server_count > 0:
            data["avg_cpu"] /= server_count
            data["avg_memory"] /= server_count
            data["avg_load"] /= server_count
            data["server_count"] = server_count

    return env_analysis


def _analyze_by_tags(server_data: dict[str, Any], client_pool: GlancesClientPool) -> dict[str, Any]:
    """Analyze server performance by tags."""
    tag_analysis: dict[str, dict[str, Any]] = {}

    for alias, data in server_data.items():
        if "error" in data:
            continue

        server_config = client_pool.servers.get(alias)
        if not server_config or not server_config.tags:
            continue

        for tag in server_config.tags:
            if tag not in tag_analysis:
                tag_analysis[tag] = {
                    "servers": [],
                    "avg_cpu": 0.0,
                    "avg_memory": 0.0,
                    "avg_load": 0.0
                }

            tag_data = tag_analysis[tag]
            tag_data["servers"].append(alias)
            tag_data["avg_cpu"] += data.get("cpu_usage", 0)
            tag_data["avg_memory"] += data.get("memory_usage", 0)
            tag_data["avg_load"] += data.get("load_normalized", 0)

    # Calculate averages
    for _tag, data in tag_analysis.items():
        server_count = len(data["servers"])
        if server_count > 0:
            data["avg_cpu"] /= server_count
            data["avg_memory"] /= server_count
            data["avg_load"] /= server_count
            data["server_count"] = server_count

    return tag_analysis


def _generate_comparison_recommendations(
    server_data: dict[str, Any],
    outliers: dict[str, list[str]],
    leaders: dict[str, list[str]],
    efficiency_scores: dict[str, Any]
) -> list[str]:
    """Generate recommendations based on server comparison."""
    recommendations = []

    # Outlier recommendations
    for metric, outlier_servers in outliers.items():
        if outlier_servers:
            recommendations.append(
                f"High {metric.replace('_', ' ')} detected on servers: {', '.join(outlier_servers)}. "
                "Investigate resource constraints or workload distribution."
            )

    # Efficiency recommendations
    if efficiency_scores:
        worst_performers = sorted(
            efficiency_scores.items(),
            key=lambda x: x[1]["overall_efficiency"]
        )[:3]

        if worst_performers and worst_performers[0][1]["overall_efficiency"] < 50:
            worst_server = worst_performers[0][0]
            recommendations.append(
                f"Server {worst_server} has low overall efficiency ({worst_performers[0][1]['overall_efficiency']:.1f}%). "
                "Consider workload redistribution or resource optimization."
            )

    # Load balancing recommendations
    cpu_values = [(alias, data.get("cpu_usage", 0)) for alias, data in server_data.items() if "error" not in data]
    if cpu_values and len(cpu_values) > 1:
        cpu_values.sort(key=lambda x: x[1])
        lowest_cpu = cpu_values[0]
        highest_cpu = cpu_values[-1]

        if highest_cpu[1] - lowest_cpu[1] > 30:  # More than 30% difference
            recommendations.append(
                f"Significant CPU usage imbalance detected. Consider redistributing workload "
                f"from {highest_cpu[0]} ({highest_cpu[1]:.1f}%) to {lowest_cpu[0]} ({lowest_cpu[1]:.1f}%)."
            )

    if not recommendations:
        recommendations.append("Server resource utilization appears well-balanced across the fleet.")

    return recommendations
