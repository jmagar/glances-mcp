"""Alert engine for Glances MCP server."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from config.models import (
    Alert, AlertRule, AlertThreshold, GlancesServer,
    MCPServerConfig, ServerStatus
)
from glances_mcp.services.glances_client import GlancesClient, GlancesClientPool
from glances_mcp.utils.helpers import generate_correlation_id, is_within_maintenance_window, safe_get
from glances_mcp.utils.logging import logger


class AlertEngine:
    """Alert evaluation and management engine."""
    
    def __init__(self, client_pool: GlancesClientPool, config: MCPServerConfig):
        self.client_pool = client_pool
        self.config = config
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
    
    def _generate_alert_id(self, server_alias: str, rule_name: str, metric_path: str) -> str:
        """Generate unique alert ID."""
        return f"{server_alias}:{rule_name}:{metric_path}"
    
    def _should_suppress_alert(self, server: GlancesServer, rule: AlertRule) -> bool:
        """Check if alert should be suppressed due to maintenance windows."""
        if not self.config.maintenance_windows:
            return False
        
        # Convert maintenance windows to dict format for helper function
        maintenance_dicts = [window.model_dump() for window in self.config.maintenance_windows]
        
        return is_within_maintenance_window(maintenance_dicts)
    
    def _is_in_cooldown(self, alert_id: str, rule: AlertRule) -> bool:
        """Check if alert is in cooldown period."""
        if alert_id not in self.alert_cooldowns:
            return False
        
        last_alert_time = self.alert_cooldowns[alert_id]
        cooldown_end = last_alert_time + timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now() < cooldown_end
    
    def _evaluate_threshold(self, value: float, threshold: AlertThreshold) -> Optional[str]:
        """Evaluate if a value triggers a threshold."""
        if threshold.comparison == "gt":
            if value >= threshold.critical:
                return "critical"
            elif value >= threshold.warning:
                return "warning"
        elif threshold.comparison == "lt":
            if value <= threshold.critical:
                return "critical"
            elif value <= threshold.warning:
                return "warning"
        elif threshold.comparison == "eq":
            if value == threshold.critical:
                return "critical"
            elif value == threshold.warning:
                return "warning"
        
        return None
    
    def _extract_metric_value(self, data: Dict[str, Any], metric_path: str) -> Optional[float]:
        """Extract metric value from nested data using dot notation."""
        return safe_get(data, metric_path)
    
    def _matches_filters(self, rule: AlertRule, server: GlancesServer) -> bool:
        """Check if server matches rule filters."""
        # Server filter
        if rule.server_filter and server.alias not in rule.server_filter:
            return False
        
        # Environment filter
        if rule.environment_filter and server.environment not in rule.environment_filter:
            return False
        
        # Tag filter
        if rule.tag_filter:
            if not any(tag in server.tags for tag in rule.tag_filter):
                return False
        
        return True
    
    async def evaluate_rules(self, server_alias: Optional[str] = None) -> List[Alert]:
        """Evaluate alert rules against current metrics."""
        new_alerts = []
        
        # Get servers to check
        if server_alias:
            servers = [self.client_pool.servers[server_alias]] if server_alias in self.client_pool.servers else []
        else:
            servers = list(self.client_pool.servers.values())
        
        for server in servers:
            if not server.enabled:
                continue
            
            client = self.client_pool.get_client(server.alias)
            if not client:
                continue
            
            try:
                # Get all metrics for this server
                all_stats = await client.get_all_stats()
                
                # Evaluate each rule
                for rule in self.config.alert_rules:
                    if not rule.enabled:
                        continue
                    
                    if not self._matches_filters(rule, server):
                        continue
                    
                    if self._should_suppress_alert(server, rule):
                        logger.debug(
                            "Alert suppressed due to maintenance window",
                            server_alias=server.alias,
                            rule_name=rule.name
                        )
                        continue
                    
                    alert_id = self._generate_alert_id(server.alias, rule.name, rule.metric_path)
                    
                    if self._is_in_cooldown(alert_id, rule):
                        logger.debug(
                            "Alert in cooldown period",
                            server_alias=server.alias,
                            rule_name=rule.name,
                            alert_id=alert_id
                        )
                        continue
                    
                    # Extract metric value
                    current_value = self._extract_metric_value(all_stats, rule.metric_path)
                    
                    if current_value is None:
                        logger.warning(
                            "Could not extract metric value",
                            server_alias=server.alias,
                            rule_name=rule.name,
                            metric_path=rule.metric_path
                        )
                        continue
                    
                    # Evaluate threshold
                    severity = self._evaluate_threshold(current_value, rule.thresholds)
                    
                    if severity:
                        # Check if this is a new alert or escalation
                        existing_alert = self.active_alerts.get(alert_id)
                        
                        if not existing_alert or existing_alert.severity != severity:
                            # Create new alert
                            threshold_value = (rule.thresholds.critical 
                                             if severity == "critical" 
                                             else rule.thresholds.warning)
                            
                            alert = Alert(
                                id=alert_id,
                                rule_name=rule.name,
                                server_alias=server.alias,
                                metric_path=rule.metric_path,
                                severity=severity,
                                current_value=current_value,
                                threshold_value=threshold_value,
                                message=self._generate_alert_message(
                                    rule, server, current_value, threshold_value, severity
                                ),
                                timestamp=datetime.now(),
                                tags={
                                    "environment": server.environment.value if server.environment else None,
                                    "region": server.region,
                                    "server_tags": server.tags
                                }
                            )
                            
                            self.active_alerts[alert_id] = alert
                            self.alert_history.append(alert)
                            new_alerts.append(alert)
                            
                            # Set cooldown
                            self.alert_cooldowns[alert_id] = datetime.now()
                            
                            logger.warning(
                                "Alert triggered",
                                server_alias=server.alias,
                                rule_name=rule.name,
                                severity=severity,
                                current_value=current_value,
                                threshold_value=threshold_value,
                                alert_id=alert_id
                            )
                    else:
                        # Check if we need to resolve an existing alert
                        if alert_id in self.active_alerts:
                            self._resolve_alert(alert_id)
            
            except Exception as e:
                logger.error(
                    "Error evaluating alerts for server",
                    server_alias=server.alias,
                    error=str(e)
                )
        
        return new_alerts
    
    def _generate_alert_message(
        self,
        rule: AlertRule,
        server: GlancesServer,
        current_value: float,
        threshold_value: float,
        severity: str
    ) -> str:
        """Generate human-readable alert message."""
        comparison_text = {
            "gt": "above",
            "lt": "below",
            "eq": "equal to"
        }.get(rule.thresholds.comparison, "compared to")
        
        unit = rule.thresholds.unit if rule.thresholds.unit else ""
        
        return (f"{severity.upper()}: {rule.metric_path} on {server.alias} "
                f"is {comparison_text} threshold. "
                f"Current: {current_value}{unit}, "
                f"Threshold: {threshold_value}{unit}")
    
    def _resolve_alert(self, alert_id: str) -> None:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_timestamp = datetime.now()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(
                "Alert resolved",
                alert_id=alert_id,
                server_alias=alert.server_alias,
                rule_name=alert.rule_name
            )
    
    def get_active_alerts(
        self,
        server_alias: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Alert]:
        """Get currently active alerts."""
        alerts = list(self.active_alerts.values())
        
        if server_alias:
            alerts = [a for a in alerts if a.server_alias == server_alias]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_history(
        self,
        server_alias: Optional[str] = None,
        severity: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Alert]:
        """Get alert history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        alerts = [a for a in self.alert_history if a.timestamp >= cutoff_time]
        
        if server_alias:
            alerts = [a for a in alerts if a.server_alias == server_alias]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp descending and limit
        alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_alerts = self.get_active_alerts()
        
        summary = {
            "total_active": len(active_alerts),
            "critical_count": len([a for a in active_alerts if a.severity == "critical"]),
            "warning_count": len([a for a in active_alerts if a.severity == "warning"]),
            "servers_with_alerts": len(set(a.server_alias for a in active_alerts)),
            "recent_alerts_24h": len(self.get_alert_history(hours=24)),
            "top_alerting_servers": self._get_top_alerting_servers(),
            "most_common_alerts": self._get_most_common_alerts()
        }
        
        return summary
    
    def _get_top_alerting_servers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get servers with most active alerts."""
        server_counts = {}
        
        for alert in self.active_alerts.values():
            server_alias = alert.server_alias
            if server_alias not in server_counts:
                server_counts[server_alias] = {"critical": 0, "warning": 0}
            server_counts[server_alias][alert.severity] += 1
        
        # Sort by total alerts (critical weighted higher)
        sorted_servers = sorted(
            server_counts.items(),
            key=lambda x: x[1]["critical"] * 2 + x[1]["warning"],
            reverse=True
        )
        
        return [
            {
                "server_alias": server,
                "critical_alerts": counts["critical"],
                "warning_alerts": counts["warning"],
                "total_alerts": counts["critical"] + counts["warning"]
            }
            for server, counts in sorted_servers[:limit]
        ]
    
    def _get_most_common_alerts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common alert types."""
        rule_counts = {}
        
        for alert in self.alert_history:
            # Only count recent alerts
            if (datetime.now() - alert.timestamp).total_seconds() < 86400:  # 24 hours
                rule_name = alert.rule_name
                if rule_name not in rule_counts:
                    rule_counts[rule_name] = 0
                rule_counts[rule_name] += 1
        
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"rule_name": rule, "count": count}
            for rule, count in sorted_rules[:limit]
        ]
    
    async def check_server_health_alerts(self) -> List[Alert]:
        """Check for server health-based alerts."""
        health_alerts = []
        
        # Get health status for all servers
        health_statuses = await self.client_pool.health_check_all()
        
        for server_alias, status in health_statuses.items():
            if status.health.status in ["warning", "critical"]:
                alert_id = self._generate_alert_id(server_alias, "server_health", "health.status")
                
                # Check if this is a new alert
                if alert_id not in self.active_alerts:
                    alert = Alert(
                        id=alert_id,
                        rule_name="server_health",
                        server_alias=server_alias,
                        metric_path="health.status",
                        severity=status.health.status,
                        current_value=1.0 if status.health.status == "critical" else 0.5,
                        threshold_value=0.0,
                        message=f"Server health check failed: {status.health.message}",
                        timestamp=datetime.now(),
                        tags={
                            "health_check": True,
                            "response_time_ms": status.response_time_ms
                        }
                    )
                    
                    self.active_alerts[alert_id] = alert
                    self.alert_history.append(alert)
                    health_alerts.append(alert)
            else:
                # Resolve health alert if it exists
                alert_id = self._generate_alert_id(server_alias, "server_health", "health.status")
                if alert_id in self.active_alerts:
                    self._resolve_alert(alert_id)
        
        return health_alerts
    
    def cleanup_old_alerts(self) -> None:
        """Clean up old alerts from history."""
        retention_days = self.config.alert_history_retention
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        # Keep alerts newer than cutoff time
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        logger.info(
            "Cleaned up old alerts",
            total_alerts=len(self.alert_history),
            retention_days=retention_days
        )
    
    async def run_continuous_monitoring(self, interval_seconds: int = 60) -> None:
        """Run continuous alert monitoring."""
        logger.info("Starting continuous alert monitoring", interval_seconds=interval_seconds)
        
        while True:
            try:
                # Evaluate all rules
                new_alerts = await self.evaluate_rules()
                
                # Check server health
                health_alerts = await self.check_server_health_alerts()
                
                if new_alerts or health_alerts:
                    logger.info(
                        "Alert evaluation completed",
                        new_alerts=len(new_alerts),
                        health_alerts=len(health_alerts),
                        total_active=len(self.active_alerts)
                    )
                
                # Cleanup old alerts periodically (every hour)
                current_time = datetime.now()
                if current_time.minute == 0:
                    self.cleanup_old_alerts()
                
            except Exception as e:
                logger.error("Error during alert monitoring", error=str(e))
            
            await asyncio.sleep(interval_seconds)