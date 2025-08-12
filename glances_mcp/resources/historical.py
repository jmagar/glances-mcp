"""Historical data resources for Glances MCP server."""

from datetime import datetime
import json
from typing import Any, cast

from fastmcp import FastMCP

from glances_mcp.services.alert_engine import AlertEngine
from glances_mcp.services.baseline_manager import BaselineManager


def register_historical_resources(
    app: FastMCP,
    baseline_manager: BaselineManager,
    alert_engine: AlertEngine
) -> None:
    """Register historical data resources with the MCP server."""

    @app.resource("glances://history/performance")
    async def performance_history() -> str:
        """Performance baseline data and historical trend analysis."""
        try:
            # Get baseline summary
            baseline_summary = baseline_manager.get_baseline_summary()

            # Get recent performance data for all servers
            performance_data = {}

            for server_alias in baseline_manager.recent_data.keys():
                server_performance = {}

                # Get trend analysis for key metrics
                for metric in baseline_manager.baseline_metrics:
                    trend = baseline_manager.get_trend_analysis(server_alias, metric)
                    if trend:
                        server_performance[metric] = {
                            "trend_direction": trend["direction"],
                            "slope": trend["slope"],
                            "confidence": trend["confidence"],
                            "recent_change_percent": trend["recent_change"]
                        }

                if server_performance:
                    performance_data[server_alias] = server_performance

            # Historical performance insights
            performance_insights = []

            if baseline_summary["total_baselines"] > 0:
                performance_insights.append(
                    f"Performance baselines available for {baseline_summary['servers_with_baselines']} servers"
                )

                if baseline_summary.get("oldest_baseline") and baseline_summary.get("newest_baseline"):
                    performance_insights.append(
                        f"Baseline data spans from {baseline_summary['oldest_baseline'][:10]} to {baseline_summary['newest_baseline'][:10]}"
                    )

            # Performance recommendations based on trends
            recommendations = []

            for server, metrics in performance_data.items():
                increasing_metrics = [m for m, data in metrics.items() if data["trend_direction"] == "increasing"]
                if len(increasing_metrics) > 2:
                    recommendations.append(
                        f"Server {server} shows increasing trends in {len(increasing_metrics)} metrics - investigate resource constraints"
                    )

            performance_resource = {
                "resource_info": {
                    "uri": "glances://history/performance",
                    "name": "Performance History and Baselines",
                    "description": "Historical performance data, baselines, and trend analysis",
                    "type": "historical_data",
                    "last_updated": datetime.now().isoformat(),
                    "format": "JSON"
                },
                "baseline_summary": baseline_summary,
                "performance_trends": performance_data,
                "insights": performance_insights,
                "recommendations": recommendations,
                "data_collection": {
                    "metrics_tracked": baseline_manager.baseline_metrics,
                    "collection_interval": "5 minutes",
                    "retention_period": f"{baseline_manager.recent_data} hours (in memory)",
                    "baseline_calculation": "Weekly rolling baseline with 95% confidence interval"
                }
            }

            return json.dumps(performance_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://history/performance",
                    "name": "Performance History and Baselines",
                    "error": str(e)
                },
                "baseline_summary": {},
                "performance_trends": {},
                "message": "Unable to load performance history"
            }
            return json.dumps(error_response, indent=2)

    @app.resource("glances://history/alerts")
    async def alerts_history() -> str:
        """Alert history and patterns with resolution tracking."""
        try:
            # Get alert summary and recent history
            alert_summary = alert_engine.get_alert_summary()
            recent_alerts = alert_engine.get_alert_history(hours=168, limit=200)  # 7 days

            # Process alert history for insights
            alert_insights: dict[str, Any] = {
                "temporal_patterns": {},
                "server_patterns": {},
                "resolution_patterns": {},
                "recurring_issues": []
            }

            # Analyze temporal patterns (by hour of day)
            hourly_distribution = [0] * 24
            daily_distribution = [0] * 7

            for alert in recent_alerts:
                hour = alert.timestamp.hour
                day = alert.timestamp.weekday()
                hourly_distribution[hour] += 1
                daily_distribution[day] += 1

            # Find peak hours and days
            peak_hour = hourly_distribution.index(max(hourly_distribution))
            peak_day = daily_distribution.index(max(daily_distribution))
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

            alert_insights["temporal_patterns"] = {
                "hourly_distribution": hourly_distribution,
                "daily_distribution": daily_distribution,
                "peak_hour": peak_hour,
                "peak_day": day_names[peak_day],
                "busiest_time": f"{day_names[peak_day]} at {peak_hour:02d}:00"
            }

            # Analyze by server
            server_alert_counts = {}
            for alert in recent_alerts:
                server = alert.server_alias
                if server not in server_alert_counts:
                    server_alert_counts[server] = {"total": 0, "critical": 0, "warning": 0, "resolved": 0}

                server_alert_counts[server]["total"] += 1
                server_alert_counts[server][alert.severity] += 1
                if alert.resolved:
                    server_alert_counts[server]["resolved"] += 1

            alert_insights["server_patterns"] = server_alert_counts

            # Resolution time analysis
            resolution_times = []
            for alert in recent_alerts:
                if alert.resolved and alert.resolved_timestamp:
                    resolution_seconds = (alert.resolved_timestamp - alert.timestamp).total_seconds()
                    resolution_times.append(resolution_seconds)

            if resolution_times:
                avg_resolution = sum(resolution_times) / len(resolution_times)
                alert_insights["resolution_patterns"] = {
                    "average_resolution_minutes": avg_resolution / 60,
                    "total_resolved_alerts": len(resolution_times),
                    "fastest_resolution_minutes": min(resolution_times) / 60,
                    "slowest_resolution_minutes": max(resolution_times) / 60
                }

            # Identify recurring issues (same rule triggered multiple times)
            rule_counts: dict[str, list[Any]] = {}
            for alert in recent_alerts:
                rule = alert.rule_name
                if rule not in rule_counts:
                    rule_counts[rule] = []
                rule_counts[rule].append(alert)

            for rule, alerts in rule_counts.items():
                if len(alerts) >= 3:  # 3 or more occurrences
                    cast(list[dict[str, Any]], alert_insights["recurring_issues"]).append({
                        "rule_name": rule,
                        "occurrences": len(alerts),
                        "servers_affected": len({a.server_alias for a in alerts}),
                        "severity_distribution": {
                            "critical": len([a for a in alerts if a.severity == "critical"]),
                            "warning": len([a for a in alerts if a.severity == "warning"])
                        }
                    })

            # Generate insights and recommendations
            insights = []
            recommendations = []

            if alert_summary["total_active"] > 0:
                insights.append(f"Currently {alert_summary['total_active']} active alerts across {alert_summary['servers_with_alerts']} servers")

            if alert_insights["recurring_issues"]:
                insights.append(f"Identified {len(alert_insights['recurring_issues'])} recurring alert patterns")
                recommendations.append("Review recurring alert patterns to identify systemic issues or threshold adjustments needed")

            if alert_insights["resolution_patterns"]:
                resolution_patterns = cast(dict[str, Any], alert_insights["resolution_patterns"])
                avg_res_min = resolution_patterns["average_resolution_minutes"]
                if avg_res_min > 60:
                    recommendations.append("Average resolution time exceeds 1 hour - consider improving alert response procedures")
                else:
                    insights.append(f"Average alert resolution time is {avg_res_min:.1f} minutes - good response performance")

            alert_history_resource = {
                "resource_info": {
                    "uri": "glances://history/alerts",
                    "name": "Alert History and Patterns",
                    "description": "Historical alert data with resolution tracking and pattern analysis",
                    "type": "historical_data",
                    "last_updated": datetime.now().isoformat(),
                    "format": "JSON"
                },
                "current_status": alert_summary,
                "historical_analysis": alert_insights,
                "insights": insights,
                "recommendations": recommendations,
                "data_scope": {
                    "history_period": "7 days",
                    "total_alerts_analyzed": len(recent_alerts),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }

            return json.dumps(alert_history_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://history/alerts",
                    "name": "Alert History and Patterns",
                    "error": str(e)
                },
                "current_status": {},
                "historical_analysis": {},
                "message": "Unable to load alert history"
            }
            return json.dumps(error_response, indent=2)

    @app.resource("glances://history/capacity")
    async def capacity_history() -> str:
        """Historical capacity utilization and growth patterns."""
        try:
            # Get capacity data from baseline manager
            capacity_data: dict[str, Any] = {}

            for server_alias in baseline_manager.recent_data.keys():
                server_capacity: dict[str, Any] = {
                    "current_utilization": {},
                    "growth_trends": {},
                    "capacity_warnings": []
                }

                # Analyze key capacity metrics
                capacity_metrics = ["cpu.total", "mem.percent"]

                for metric in capacity_metrics:
                    # Get current baseline and trend
                    baseline = baseline_manager.get_cached_baseline(server_alias, metric)
                    trend = baseline_manager.get_trend_analysis(server_alias, metric, 24 * 7)  # 7 days

                    if baseline and trend:
                        current_util = cast(dict[str, Any], server_capacity["current_utilization"])
                        current_util[metric] = {
                            "baseline_value": baseline.baseline_value,
                            "std_deviation": baseline.std_deviation,
                            "confidence_interval": baseline.confidence_interval
                        }

                        growth_trends = cast(dict[str, Any], server_capacity["growth_trends"])
                        growth_trends[metric] = {
                            "direction": trend["direction"],
                            "recent_change_percent": trend["recent_change"],
                            "confidence": trend["confidence"]
                        }

                        # Generate warnings based on trends
                        if trend["direction"] == "increasing" and trend["confidence"] > 0.7:
                            if baseline.baseline_value > 70 and trend["recent_change"] > 10:
                                capacity_warnings = cast(list[str], server_capacity["capacity_warnings"])
                                capacity_warnings.append(
                                    f"{metric}: High utilization ({baseline.baseline_value:.1f}%) with increasing trend (+{trend['recent_change']:.1f}%)"
                                )

                capacity_data[server_alias] = server_capacity

            # Generate fleet-wide capacity insights
            fleet_insights = {
                "servers_analyzed": len(capacity_data),
                "servers_with_warnings": len([s for s in capacity_data.values() if s["capacity_warnings"]]),
                "metrics_trending_up": 0,
                "average_cpu_utilization": 0,
                "average_memory_utilization": 0
            }

            cpu_values = []
            memory_values = []

            for server_data in capacity_data.values():
                server_dict = cast(dict[str, Any], server_data)
                current_util = cast(dict[str, Any], server_dict["current_utilization"])
                if "cpu.total" in current_util:
                    cpu_metric = cast(dict[str, Any], current_util["cpu.total"])
                    cpu_values.append(cpu_metric["baseline_value"])
                if "mem.percent" in current_util:
                    mem_metric = cast(dict[str, Any], current_util["mem.percent"])
                    memory_values.append(mem_metric["baseline_value"])

                # Count increasing trends
                server_dict = cast(dict[str, Any], server_data)
                growth_trends = cast(dict[str, Any], server_dict["growth_trends"])
                for metric_trend in growth_trends.values():
                    trend_dict = cast(dict[str, Any], metric_trend)
                    if trend_dict["direction"] == "increasing":
                        fleet_insights["metrics_trending_up"] += 1

            if cpu_values:
                fleet_insights["average_cpu_utilization"] = sum(cpu_values) / len(cpu_values)
            if memory_values:
                fleet_insights["average_memory_utilization"] = sum(memory_values) / len(memory_values)

            # Capacity planning recommendations
            recommendations = []

            if fleet_insights["servers_with_warnings"] > 0:
                recommendations.append(
                    f"{fleet_insights['servers_with_warnings']} servers have capacity warnings - review resource allocation"
                )

            if fleet_insights["average_cpu_utilization"] > 70:
                recommendations.append("Fleet average CPU utilization exceeds 70% - consider capacity expansion")

            if fleet_insights["average_memory_utilization"] > 80:
                recommendations.append("Fleet average memory utilization exceeds 80% - monitor for memory pressure")

            if fleet_insights["metrics_trending_up"] > fleet_insights["servers_analyzed"]:
                recommendations.append("Multiple metrics showing upward trends - investigate workload increases")

            capacity_history_resource = {
                "resource_info": {
                    "uri": "glances://history/capacity",
                    "name": "Capacity History and Growth Patterns",
                    "description": "Historical capacity utilization with growth trend analysis",
                    "type": "historical_data",
                    "last_updated": datetime.now().isoformat(),
                    "format": "JSON"
                },
                "server_capacity_data": capacity_data,
                "fleet_insights": fleet_insights,
                "recommendations": recommendations,
                "analysis_parameters": {
                    "metrics_analyzed": ["cpu.total", "mem.percent"],
                    "trend_analysis_window": "7 days",
                    "baseline_confidence_level": "95%",
                    "warning_thresholds": {
                        "high_utilization": 70,
                        "significant_growth": 10
                    }
                }
            }

            return json.dumps(capacity_history_resource, indent=2)

        except Exception as e:
            error_response = {
                "resource_info": {
                    "uri": "glances://history/capacity",
                    "name": "Capacity History and Growth Patterns",
                    "error": str(e)
                },
                "server_capacity_data": {},
                "fleet_insights": {},
                "message": "Unable to load capacity history"
            }
            return json.dumps(error_response, indent=2)
