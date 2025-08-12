"""Health score calculation service for Glances MCP server."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from config.models import GlancesServer
from glances_mcp.services.glances_client import GlancesClient
from glances_mcp.utils.helpers import safe_get
from glances_mcp.utils.logging import logger
from glances_mcp.utils.metrics import MetricsCalculator


class HealthCalculator:
    """Service for calculating composite health scores."""
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        
        # Default health scoring weights
        self.default_weights = {
            "cpu": 0.25,
            "memory": 0.25,
            "disk": 0.25,
            "network": 0.15,
            "load": 0.10
        }
        
        # Critical thresholds for health scoring
        self.critical_thresholds = {
            "cpu_usage": 90.0,
            "memory_usage": 90.0,
            "disk_usage": 95.0,
            "load_normalized": 2.0,
            "network_error_rate": 1.0
        }
    
    async def calculate_server_health(
        self,
        client: GlancesClient,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive health score for a server."""
        if weights is None:
            weights = self.default_weights.copy()
        
        start_time = datetime.now()
        health_data = {
            "server_alias": client.server.alias,
            "timestamp": start_time.isoformat(),
            "overall_score": 0.0,
            "status": "unknown",
            "component_scores": {},
            "critical_issues": [],
            "warnings": [],
            "metrics": {}
        }
        
        try:
            # Collect all necessary metrics
            metrics = await self._collect_health_metrics(client)
            health_data["metrics"] = metrics
            
            # Calculate component scores
            component_scores = {}
            
            # CPU Health Score
            if "cpu" in metrics:
                cpu_score = self._calculate_cpu_health_score(metrics["cpu"])
                component_scores["cpu"] = cpu_score
                
                if cpu_score["score"] < 20:
                    health_data["critical_issues"].append("High CPU usage")
                elif cpu_score["score"] < 50:
                    health_data["warnings"].append("Elevated CPU usage")
            
            # Memory Health Score
            if "memory" in metrics:
                memory_score = self._calculate_memory_health_score(metrics["memory"])
                component_scores["memory"] = memory_score
                
                if memory_score["score"] < 20:
                    health_data["critical_issues"].append("High memory usage")
                elif memory_score["score"] < 50:
                    health_data["warnings"].append("Elevated memory usage")
            
            # Disk Health Score
            if "disks" in metrics:
                disk_score = self._calculate_disk_health_score(metrics["disks"])
                component_scores["disk"] = disk_score
                
                if disk_score["score"] < 20:
                    health_data["critical_issues"].append("High disk usage")
                elif disk_score["score"] < 50:
                    health_data["warnings"].append("Elevated disk usage")
            
            # Network Health Score
            if "network" in metrics:
                network_score = self._calculate_network_health_score(metrics["network"])
                component_scores["network"] = network_score
                
                if network_score["score"] < 50:
                    health_data["warnings"].append("Network errors detected")
            
            # Load Health Score
            if "load" in metrics and "system" in metrics:
                cpu_count = safe_get(metrics["system"], "cpucount", 1)
                load_score = self._calculate_load_health_score(metrics["load"], cpu_count)
                component_scores["load"] = load_score
                
                if load_score["score"] < 20:
                    health_data["critical_issues"].append("High system load")
                elif load_score["score"] < 50:
                    health_data["warnings"].append("Elevated system load")
            
            health_data["component_scores"] = component_scores
            
            # Calculate overall score
            overall_score = self._calculate_weighted_score(component_scores, weights)
            health_data["overall_score"] = overall_score
            
            # Determine overall status
            health_data["status"] = self._determine_health_status(
                overall_score,
                health_data["critical_issues"],
                health_data["warnings"]
            )
            
            calculation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.debug(
                "Health score calculated",
                server_alias=client.server.alias,
                overall_score=overall_score,
                status=health_data["status"],
                calculation_time_ms=calculation_time_ms
            )
        
        except Exception as e:
            logger.error(
                "Error calculating health score",
                server_alias=client.server.alias,
                error=str(e)
            )
            health_data["status"] = "error"
            health_data["critical_issues"].append(f"Health calculation failed: {str(e)}")
        
        return health_data
    
    async def _collect_health_metrics(self, client: GlancesClient) -> Dict[str, Any]:
        """Collect all metrics needed for health calculation."""
        metrics = {}
        
        try:
            # System information
            system_data = await client.get_system_info()
            metrics["system"] = system_data
            
            # CPU metrics
            cpu_data = await client.get_cpu_info()
            metrics["cpu"] = cpu_data
            
            # Memory metrics
            memory_data = await client.get_memory_info()
            metrics["memory"] = memory_data
            
            # Load averages
            load_data = await client.get_load_average()
            metrics["load"] = load_data
            
            # Disk usage
            disk_data = await client.get_disk_usage()
            metrics["disks"] = disk_data
            
            # Network interfaces
            network_data = await client.get_network_interfaces()
            metrics["network"] = network_data
        
        except Exception as e:
            logger.warning(
                "Error collecting some health metrics",
                server_alias=client.server.alias,
                error=str(e)
            )
        
        return metrics
    
    def _calculate_cpu_health_score(self, cpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate CPU health score and details."""
        total_usage = safe_get(cpu_data, "total", 0)
        user_usage = safe_get(cpu_data, "user", 0)
        system_usage = safe_get(cpu_data, "system", 0)
        iowait = safe_get(cpu_data, "iowait", 0)
        steal = safe_get(cpu_data, "steal", 0)
        
        # Base score from total usage (inverted)
        base_score = max(0, 100 - total_usage)
        
        # Apply penalties
        penalties = 0
        
        # High I/O wait penalty
        if iowait > 20:
            penalties += min(iowait, 30)  # Cap at 30 points
        elif iowait > 10:
            penalties += iowait * 0.5
        
        # Steal time penalty (virtualization overhead)
        if steal > 5:
            penalties += steal * 2
        
        # High system usage penalty
        if system_usage > 50:
            penalties += (system_usage - 50) * 0.5
        
        final_score = max(0, base_score - penalties)
        
        return {
            "score": final_score,
            "details": {
                "total_usage": total_usage,
                "user_usage": user_usage,
                "system_usage": system_usage,
                "iowait": iowait,
                "steal": steal,
                "penalties_applied": penalties
            },
            "issues": self._identify_cpu_issues(cpu_data)
        }
    
    def _calculate_memory_health_score(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate memory health score and details."""
        percent_used = safe_get(memory_data, "percent", 0)
        available = safe_get(memory_data, "available", 0)
        total = safe_get(memory_data, "total", 1)
        
        # Base score from usage percentage (inverted)
        base_score = max(0, 100 - percent_used)
        
        # Additional considerations
        available_gb = available / (1024**3) if available else 0
        
        # Penalty for very low available memory
        if available_gb < 0.5:  # Less than 500MB available
            base_score = min(base_score, 20)  # Cap at 20
        elif available_gb < 1.0:  # Less than 1GB available
            base_score = min(base_score, 40)  # Cap at 40
        
        return {
            "score": base_score,
            "details": {
                "percent_used": percent_used,
                "available_gb": available_gb,
                "total_gb": total / (1024**3) if total else 0
            },
            "issues": self._identify_memory_issues(memory_data)
        }
    
    def _calculate_disk_health_score(self, disk_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate disk health score and details."""
        if not disk_data:
            return {"score": 100, "details": {}, "issues": []}
        
        disk_scores = []
        critical_disks = []
        warning_disks = []
        
        for disk in disk_data:
            mount_point = safe_get(disk, "mnt_point", "unknown")
            percent_used = safe_get(disk, "percent", 0)
            
            # Score for this disk (inverted usage)
            disk_score = max(0, 100 - percent_used)
            disk_scores.append(disk_score)
            
            # Track problematic disks
            if percent_used >= 95:
                critical_disks.append(f"{mount_point} ({percent_used:.1f}%)")
            elif percent_used >= 85:
                warning_disks.append(f"{mount_point} ({percent_used:.1f}%)")
        
        # Overall score is the minimum disk score (worst case)
        overall_score = min(disk_scores) if disk_scores else 100
        
        # But don't let one full disk completely tank the score
        # unless it's the root filesystem
        root_disk_score = None
        for disk in disk_data:
            if safe_get(disk, "mnt_point") == "/":
                root_disk_score = max(0, 100 - safe_get(disk, "percent", 0))
                break
        
        if root_disk_score is not None:
            # Weight root disk more heavily
            overall_score = (root_disk_score * 0.7) + (overall_score * 0.3)
        
        issues = []
        if critical_disks:
            issues.append(f"Critical disk usage: {', '.join(critical_disks)}")
        if warning_disks:
            issues.append(f"High disk usage: {', '.join(warning_disks)}")
        
        return {
            "score": overall_score,
            "details": {
                "disk_count": len(disk_data),
                "critical_disks": critical_disks,
                "warning_disks": warning_disks,
                "worst_usage": max((safe_get(d, "percent", 0) for d in disk_data), default=0)
            },
            "issues": issues
        }
    
    def _calculate_network_health_score(self, network_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate network health score and details."""
        if not network_data:
            return {"score": 100, "details": {}, "issues": []}
        
        total_errors = 0
        total_packets = 0
        interfaces_with_errors = []
        
        for interface in network_data:
            interface_name = safe_get(interface, "interface_name", "unknown")
            rx_errors = safe_get(interface, "rx_errors", 0)
            tx_errors = safe_get(interface, "tx_errors", 0)
            rx_packets = safe_get(interface, "rx_packets", 0)
            tx_packets = safe_get(interface, "tx_packets", 0)
            
            interface_errors = rx_errors + tx_errors
            interface_packets = rx_packets + tx_packets
            
            total_errors += interface_errors
            total_packets += interface_packets
            
            if interface_errors > 0 and interface_packets > 0:
                error_rate = (interface_errors / interface_packets) * 100
                if error_rate > 0.1:  # More than 0.1% error rate
                    interfaces_with_errors.append(f"{interface_name} ({error_rate:.2f}%)")
        
        # Calculate overall error rate
        if total_packets > 0:
            overall_error_rate = (total_errors / total_packets) * 100
        else:
            overall_error_rate = 0
        
        # Score based on error rate
        if overall_error_rate == 0:
            score = 100
        elif overall_error_rate < 0.01:  # Less than 0.01%
            score = 95
        elif overall_error_rate < 0.1:   # Less than 0.1%
            score = 80
        elif overall_error_rate < 1.0:   # Less than 1%
            score = 60
        else:
            score = max(0, 40 - (overall_error_rate * 5))
        
        issues = []
        if interfaces_with_errors:
            issues.append(f"Network errors on: {', '.join(interfaces_with_errors)}")
        
        return {
            "score": score,
            "details": {
                "interface_count": len(network_data),
                "total_errors": total_errors,
                "total_packets": total_packets,
                "error_rate_percent": overall_error_rate,
                "interfaces_with_errors": len(interfaces_with_errors)
            },
            "issues": issues
        }
    
    def _calculate_load_health_score(self, load_data: Dict[str, Any], cpu_count: int) -> Dict[str, Any]:
        """Calculate system load health score."""
        load_1min = safe_get(load_data, "min1", 0)
        load_5min = safe_get(load_data, "min5", 0)
        load_15min = safe_get(load_data, "min15", 0)
        
        # Normalize by CPU count
        normalized_loads = {
            "1min": load_1min / cpu_count,
            "5min": load_5min / cpu_count,
            "15min": load_15min / cpu_count
        }
        
        # Use 5-minute load as primary indicator
        primary_load = normalized_loads["5min"]
        
        # Score based on normalized load
        if primary_load <= 0.5:
            score = 100
        elif primary_load <= 0.7:
            score = 90
        elif primary_load <= 1.0:
            score = 80 - ((primary_load - 0.7) * 100)
        elif primary_load <= 2.0:
            score = 50 - ((primary_load - 1.0) * 25)
        else:
            score = max(0, 25 - ((primary_load - 2.0) * 12.5))
        
        issues = []
        if primary_load > 2.0:
            issues.append(f"Very high system load ({primary_load:.2f})")
        elif primary_load > 1.0:
            issues.append(f"High system load ({primary_load:.2f})")
        
        return {
            "score": score,
            "details": {
                "load_1min": load_1min,
                "load_5min": load_5min,
                "load_15min": load_15min,
                "cpu_count": cpu_count,
                "normalized_loads": normalized_loads,
                "primary_load_normalized": primary_load
            },
            "issues": issues
        }
    
    def _calculate_weighted_score(
        self,
        component_scores: Dict[str, Dict[str, Any]],
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted composite score."""
        total_score = 0.0
        total_weight = 0.0
        
        for component, weight in weights.items():
            if component in component_scores:
                score = component_scores[component].get("score", 0)
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_health_status(
        self,
        overall_score: float,
        critical_issues: List[str],
        warnings: List[str]
    ) -> str:
        """Determine overall health status."""
        if critical_issues or overall_score < 20:
            return "critical"
        elif warnings or overall_score < 50:
            return "warning"
        elif overall_score < 80:
            return "degraded"
        else:
            return "healthy"
    
    def _identify_cpu_issues(self, cpu_data: Dict[str, Any]) -> List[str]:
        """Identify specific CPU-related issues."""
        issues = []
        
        total_usage = safe_get(cpu_data, "total", 0)
        iowait = safe_get(cpu_data, "iowait", 0)
        steal = safe_get(cpu_data, "steal", 0)
        system_usage = safe_get(cpu_data, "system", 0)
        
        if total_usage > 90:
            issues.append(f"Very high CPU usage ({total_usage:.1f}%)")
        elif total_usage > 80:
            issues.append(f"High CPU usage ({total_usage:.1f}%)")
        
        if iowait > 20:
            issues.append(f"High I/O wait time ({iowait:.1f}%)")
        
        if steal > 10:
            issues.append(f"High steal time - possible virtualization issues ({steal:.1f}%)")
        
        if system_usage > 50:
            issues.append(f"High system CPU usage ({system_usage:.1f}%)")
        
        return issues
    
    def _identify_memory_issues(self, memory_data: Dict[str, Any]) -> List[str]:
        """Identify specific memory-related issues."""
        issues = []
        
        percent_used = safe_get(memory_data, "percent", 0)
        available = safe_get(memory_data, "available", 0)
        
        if percent_used > 95:
            issues.append(f"Critical memory usage ({percent_used:.1f}%)")
        elif percent_used > 85:
            issues.append(f"High memory usage ({percent_used:.1f}%)")
        
        available_gb = available / (1024**3) if available else 0
        if available_gb < 0.5:
            issues.append(f"Very low available memory ({available_gb:.1f} GB)")
        
        return issues