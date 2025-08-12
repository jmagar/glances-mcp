"""Alert management tools for Glances MCP server."""

from datetime import datetime
from typing import Any, cast

from fastmcp import FastMCP

from glances_mcp.config.validation import InputValidator
from glances_mcp.services.alert_engine import AlertEngine
from glances_mcp.services.glances_client import GlancesClientPool
from glances_mcp.utils.logging import logger, performance_logger


def register_alert_management_tools(
    app: FastMCP,
    client_pool: GlancesClientPool,
    alert_engine: AlertEngine
) -> None:
    """Register alert management tools with the MCP server."""

    @app.tool()
    async def check_alert_conditions(
        server_alias: str | None = None,
        severity: str | None = None
    ) -> dict[str, Any]:
        """Evaluate current metrics against alert thresholds and return active alerts."""
        start_time = datetime.now()

        try:
            # Validate parameters
            InputValidator.validate_tool_params(
                "check_alert_conditions",
                {
                    "server_alias": server_alias,
                    "severity": severity
                }
            )

            # Trigger alert evaluation
            new_alerts = await alert_engine.evaluate_rules(server_alias)

            # Get active alerts (filtered by parameters)
            active_alerts = alert_engine.get_active_alerts(server_alias, severity)

            # Get alert summary
            alert_summary = alert_engine.get_alert_summary()

            # Format alerts for response
            formatted_alerts = []
            for alert in active_alerts:
                formatted_alert = {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "server_alias": alert.server_alias,
                    "metric_path": alert.metric_path,
                    "severity": alert.severity,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_timestamp": (
                        alert.resolved_timestamp.isoformat()
                        if alert.resolved_timestamp else None
                    ),
                    "tags": alert.tags,
                    "age_seconds": (datetime.now() - alert.timestamp).total_seconds()
                }
                formatted_alerts.append(formatted_alert)

            # Sort by severity and timestamp
            severity_order = {"critical": 0, "warning": 1}
            formatted_alerts.sort(key=lambda a: (
                severity_order.get(cast(dict[str, Any], a)["severity"], 2),
                cast(dict[str, Any], a)["timestamp"]
            ))

            result = {
                "active_alerts": formatted_alerts,
                "new_alerts_triggered": len(new_alerts),
                "evaluation_timestamp": datetime.now().isoformat(),
                "summary": alert_summary,
                "filters_applied": {
                    "server_alias": server_alias,
                    "severity": severity
                }
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("check_alert_conditions", duration_ms, True)

            return result

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("check_alert_conditions", duration_ms, False)
            logger.error("Error in check_alert_conditions", server_alias=server_alias, error=str(e))
            raise

    @app.tool()
    async def get_alert_history(
        server_alias: str | None = None,
        severity: str | None = None,
        hours: int = 24,
        limit: int = 100
    ) -> dict[str, Any]:
        """Get historical alert data with filtering options."""
        start_time = datetime.now()

        try:
            # Validate parameters
            if hours < 1 or hours > 168:  # Max 7 days
                raise ValueError("hours must be between 1 and 168 (7 days)")

            if limit < 1 or limit > 1000:
                raise ValueError("limit must be between 1 and 1000")

            # Get alert history
            historical_alerts = alert_engine.get_alert_history(
                server_alias, severity, hours, limit
            )

            # Format alerts for response
            formatted_alerts = []
            resolution_times = []

            for alert in historical_alerts:
                formatted_alert = {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "server_alias": alert.server_alias,
                    "metric_path": alert.metric_path,
                    "severity": alert.severity,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "message": alert.message,
                    "triggered_at": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": (
                        alert.resolved_timestamp.isoformat()
                        if alert.resolved_timestamp else None
                    ),
                    "tags": alert.tags
                }

                # Calculate resolution time if resolved
                if alert.resolved and alert.resolved_timestamp:
                    resolution_seconds = (
                        alert.resolved_timestamp - alert.timestamp
                    ).total_seconds()
                    formatted_alert["resolution_time_seconds"] = resolution_seconds
                    formatted_alert["resolution_time_minutes"] = resolution_seconds / 60
                    resolution_times.append(resolution_seconds)

                formatted_alerts.append(formatted_alert)

            # Calculate statistics
            total_alerts = len(formatted_alerts)
            resolved_alerts = len([a for a in formatted_alerts if a["resolved"]])
            critical_alerts = len([a for a in formatted_alerts if a["severity"] == "critical"])
            warning_alerts = len([a for a in formatted_alerts if a["severity"] == "warning"])

            # Calculate mean time to resolution
            mttr_minutes = None
            if resolution_times:
                mttr_minutes = (sum(resolution_times) / len(resolution_times)) / 60

            # Group by server for analysis
            alerts_by_server: dict[str, list[dict[str, Any]]] = {}
            for alert_data in formatted_alerts:
                alert_dict = cast(dict[str, Any], alert_data)
                server = alert_dict["server_alias"]
                if server not in alerts_by_server:
                    alerts_by_server[server] = []
                alerts_by_server[server].append(alert_dict)

            # Group by rule for analysis
            alerts_by_rule: dict[str, list[dict[str, Any]]] = {}
            for alert_data in formatted_alerts:
                alert_dict = cast(dict[str, Any], alert_data)
                rule = alert_dict["rule_name"]
                if rule not in alerts_by_rule:
                    alerts_by_rule[rule] = []
                alerts_by_rule[rule].append(alert_dict)

            result = {
                "alerts": formatted_alerts,
                "query_parameters": {
                    "server_alias": server_alias,
                    "severity": severity,
                    "hours": hours,
                    "limit": limit
                },
                "statistics": {
                    "total_alerts": total_alerts,
                    "resolved_alerts": resolved_alerts,
                    "active_alerts": total_alerts - resolved_alerts,
                    "critical_alerts": critical_alerts,
                    "warning_alerts": warning_alerts,
                    "resolution_rate_percent": (
                        (resolved_alerts / total_alerts * 100)
                        if total_alerts > 0 else 0
                    ),
                    "mean_time_to_resolution_minutes": mttr_minutes,
                    "servers_with_alerts": len(alerts_by_server),
                    "unique_alert_rules": len(alerts_by_rule)
                },
                "analysis": {
                    "alerts_by_server": {
                        server: len(alerts)
                        for server, alerts in alerts_by_server.items()
                    },
                    "alerts_by_rule": {
                        rule: len(alerts)
                        for rule, alerts in alerts_by_rule.items()
                    },
                    "top_alerting_servers": sorted(
                        alerts_by_server.items(),
                        key=lambda x: len(x[1]),
                        reverse=True
                    )[:5],
                    "most_frequent_rules": sorted(
                        alerts_by_rule.items(),
                        key=lambda x: len(x[1]),
                        reverse=True
                    )[:5]
                }
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_alert_history", duration_ms, True)

            return result

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_alert_history", duration_ms, False)
            logger.error("Error in get_alert_history",
                        server_alias=server_alias, hours=hours, error=str(e))
            raise

    @app.tool()
    async def get_alert_summary() -> dict[str, Any]:
        """Get comprehensive alert summary and statistics."""
        start_time = datetime.now()

        try:
            # Get summary from alert engine
            summary = alert_engine.get_alert_summary()

            # Get active alerts for detailed breakdown
            active_alerts = alert_engine.get_active_alerts()

            # Enhance summary with additional details
            recent_history = alert_engine.get_alert_history(hours=24)
            alerts_last_hour = alert_engine.get_alert_history(hours=1)

            # Calculate trends
            alert_trend = "stable"
            if len(alerts_last_hour) > len(recent_history) / 24 * 2:  # More than 2x hourly average
                alert_trend = "increasing"
            elif len(alerts_last_hour) == 0 and len(recent_history) > 0:
                alert_trend = "decreasing"

            # Categorize active alerts by age
            now = datetime.now()
            new_alerts = []  # < 1 hour
            recent_alerts = []  # 1-6 hours
            old_alerts = []  # > 6 hours

            for alert in active_alerts:
                age_hours = (now - alert.timestamp).total_seconds() / 3600
                if age_hours < 1:
                    new_alerts.append(alert)
                elif age_hours < 6:
                    recent_alerts.append(alert)
                else:
                    old_alerts.append(alert)

            # Enhanced summary
            enhanced_summary = {
                "timestamp": datetime.now().isoformat(),
                "alert_counts": {
                    "total_active": summary["total_active"],
                    "critical_active": summary["critical_count"],
                    "warning_active": summary["warning_count"],
                    "new_alerts_last_hour": len(new_alerts),
                    "recent_alerts_1_6h": len(recent_alerts),
                    "old_alerts_over_6h": len(old_alerts),
                    "alerts_last_24h": len(recent_history)
                },
                "server_impact": {
                    "servers_with_alerts": summary["servers_with_alerts"],
                    "total_monitored_servers": len(client_pool.get_enabled_clients()),
                    "percentage_servers_affected": (
                        (summary["servers_with_alerts"] / len(client_pool.get_enabled_clients()) * 100)
                        if len(client_pool.get_enabled_clients()) > 0 else 0
                    ),
                    "top_alerting_servers": summary["top_alerting_servers"]
                },
                "alert_patterns": {
                    "trend_last_24h": alert_trend,
                    "most_common_alerts": summary["most_common_alerts"],
                    "alerts_by_severity": {
                        "critical": len([a for a in recent_history if a.severity == "critical"]),
                        "warning": len([a for a in recent_history if a.severity == "warning"])
                    }
                },
                "alert_health": {
                    "status": "healthy" if summary["critical_count"] == 0 else "critical" if summary["critical_count"] > 3 else "warning",
                    "needs_attention": summary["critical_count"] > 0 or len(old_alerts) > 0,
                    "stale_alerts": len(old_alerts),
                    "escalation_candidates": len([
                        alert for alert in old_alerts
                        if alert.severity == "warning" and (now - alert.timestamp).total_seconds() > 21600  # 6 hours
                    ])
                },
                "recommendations": cast(list[str], [])
            }

            # Generate recommendations
            recommendations_list = cast(list[str], enhanced_summary["recommendations"])
            alert_counts = cast(dict[str, Any], enhanced_summary["alert_counts"])
            if alert_counts["critical_active"] > 0:
                recommendations_list.append(
                    f"Immediate attention required: {alert_counts['critical_active']} critical alerts active"
                )

            if len(old_alerts) > 0:
                recommendations_list.append(
                    f"Review {len(old_alerts)} long-running alerts that may need attention or threshold adjustment"
                )

            if alert_trend == "increasing":
                recommendations_list.append(
                    "Alert frequency is increasing - investigate potential issues or adjust thresholds"
                )

            server_impact = cast(dict[str, Any], enhanced_summary["server_impact"])
            if server_impact["percentage_servers_affected"] > 50:
                recommendations_list.append(
                    "More than 50% of servers have alerts - investigate systemic issues"
                )

            if not recommendations_list:
                recommendations_list.append("No immediate action required - monitoring is healthy")

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_alert_summary", duration_ms, True)

            return enhanced_summary

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_alert_summary", duration_ms, False)
            logger.error("Error in get_alert_summary", error=str(e))
            raise

    @app.tool()
    async def analyze_alert_patterns(
        hours: int = 168,  # 7 days
        min_occurrences: int = 3
    ) -> dict[str, Any]:
        """Analyze patterns in alert history to identify recurring issues."""
        start_time = datetime.now()

        try:
            if hours < 1 or hours > 720:  # Max 30 days
                raise ValueError("hours must be between 1 and 720 (30 days)")

            # Get extended alert history
            alert_history = alert_engine.get_alert_history(hours=hours, limit=1000)

            if not alert_history:
                return {
                    "message": "No alert history available for analysis",
                    "analysis_period_hours": hours,
                    "timestamp": datetime.now().isoformat()
                }

            # Pattern analysis
            patterns: dict[str, Any] = {
                "recurring_alerts": {},
                "server_patterns": {},
                "time_patterns": {},
                "correlation_patterns": []
            }

            # Group alerts by rule and server for recurring pattern detection
            rule_server_combinations: dict[str, list[Any]] = {}
            for alert in alert_history:
                key = f"{alert.rule_name}:{alert.server_alias}"
                if key not in rule_server_combinations:
                    rule_server_combinations[key] = []
                rule_server_combinations[key].append(alert)

            # Identify recurring alerts
            for combination, alerts in rule_server_combinations.items():
                if len(alerts) >= min_occurrences:
                    rule_name, server_alias = combination.split(":")

                    # Calculate time between alerts
                    sorted_alerts = sorted(alerts, key=lambda a: a.timestamp)
                    intervals = []
                    for i in range(1, len(sorted_alerts)):
                        interval_hours = (
                            sorted_alerts[i].timestamp - sorted_alerts[i-1].timestamp
                        ).total_seconds() / 3600
                        intervals.append(interval_hours)

                    avg_interval = sum(intervals) / len(intervals) if intervals else 0

                    recurring_alerts = cast(dict[str, Any], patterns["recurring_alerts"])
                    recurring_alerts[combination] = {
                        "rule_name": rule_name,
                        "server_alias": server_alias,
                        "occurrences": len(alerts),
                        "first_occurrence": sorted_alerts[0].timestamp.isoformat(),
                        "last_occurrence": sorted_alerts[-1].timestamp.isoformat(),
                        "average_interval_hours": round(avg_interval, 2),
                        "severity_distribution": {
                            "critical": len([a for a in alerts if a.severity == "critical"]),
                            "warning": len([a for a in alerts if a.severity == "warning"])
                        },
                        "pattern_type": (
                            "frequent" if avg_interval < 6 else
                            "regular" if avg_interval < 24 else
                            "periodic"
                        )
                    }

            # Server-specific patterns
            server_alert_counts: dict[str, dict[str, Any]] = {}
            for alert in alert_history:
                server = alert.server_alias
                if server not in server_alert_counts:
                    server_alert_counts[server] = {"total": 0, "critical": 0, "warning": 0, "rules": set()}

                counts = server_alert_counts[server]
                counts["total"] += 1
                counts[alert.severity] += 1
                cast(set[str], counts["rules"]).add(alert.rule_name)

            # Identify problematic servers
            for server, counts in server_alert_counts.items():
                if counts["total"] >= min_occurrences:
                    server_patterns = cast(dict[str, Any], patterns["server_patterns"])
                    server_patterns[server] = {
                        "total_alerts": counts["total"],
                        "critical_alerts": counts["critical"],
                        "warning_alerts": counts["warning"],
                        "unique_rules_triggered": len(cast(set[str], counts["rules"])),
                        "alert_density": counts["total"] / hours,  # alerts per hour
                        "severity_ratio": (
                            counts["critical"] / counts["total"]
                            if counts["total"] > 0 else 0
                        )
                    }

            # Time-based patterns (hour of day analysis)
            hourly_distribution = [0] * 24
            for alert in alert_history:
                hour = alert.timestamp.hour
                hourly_distribution[hour] += 1

            # Find peak hours
            peak_hours = []
            avg_hourly = sum(hourly_distribution) / 24
            for hour, count in enumerate(hourly_distribution):
                if count > avg_hourly * 1.5:  # 50% above average
                    peak_hours.append({"hour": hour, "alert_count": count})

            time_patterns = cast(dict[str, Any], patterns["time_patterns"])
            time_patterns.update({
                "hourly_distribution": hourly_distribution,
                "peak_hours": sorted(peak_hours, key=lambda x: x["alert_count"], reverse=True),
                "busiest_hour": hourly_distribution.index(max(hourly_distribution)),
                "quietest_hour": hourly_distribution.index(min(hourly_distribution))
            })

            # Generate insights and recommendations
            insights = []
            recommendations = []

            if patterns["recurring_alerts"]:
                frequent_alerts = [
                    p for p in patterns["recurring_alerts"].values()
                    if p["pattern_type"] == "frequent"
                ]
                if frequent_alerts:
                    insights.append(
                        f"Found {len(frequent_alerts)} frequently recurring alert patterns (< 6h intervals)"
                    )
                    recommendations.append("Review alert thresholds for frequently recurring alerts")

            if patterns["server_patterns"]:
                high_density_servers = [
                    (server, data) for server, data in patterns["server_patterns"].items()
                    if data["alert_density"] > 1  # More than 1 alert per hour on average
                ]
                if high_density_servers:
                    insights.append(
                        f"Identified {len(high_density_servers)} servers with high alert density"
                    )
                    recommendations.append("Investigate servers with consistently high alert volumes")

            if patterns["time_patterns"]["peak_hours"]:
                insights.append(
                    f"Alert activity peaks at hour {patterns['time_patterns']['busiest_hour']}:00"
                )
                recommendations.append("Consider scheduled maintenance during quieter hours")

            result = {
                "analysis_summary": {
                    "total_alerts_analyzed": len(alert_history),
                    "analysis_period_hours": hours,
                    "recurring_patterns_found": len(patterns["recurring_alerts"]),
                    "servers_with_patterns": len(patterns["server_patterns"]),
                    "time_patterns_detected": len(patterns["time_patterns"]["peak_hours"]),
                    "timestamp": datetime.now().isoformat()
                },
                "patterns": patterns,
                "insights": insights,
                "recommendations": recommendations
            }

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("analyze_alert_patterns", duration_ms, True)

            return result

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("analyze_alert_patterns", duration_ms, False)
            logger.error("Error in analyze_alert_patterns", hours=hours, error=str(e))
            raise
