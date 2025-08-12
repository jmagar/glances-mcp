"""Metrics calculation utilities for Glances MCP server."""

from datetime import datetime, timedelta
import statistics
from typing import Any

from glances_mcp.config.models import MetricPoint, PerformanceBaseline


class MetricsCalculator:
    """Utility class for metrics calculations."""

    @staticmethod
    def calculate_cpu_score(cpu_data: dict[str, Any]) -> float:
        """Calculate CPU health score (0-100, higher is better)."""
        try:
            total_usage = cpu_data.get("total", 0)
            iowait = cpu_data.get("iowait", 0)

            # Base score from CPU usage (inverse)
            usage_score = max(0, 100 - total_usage)

            # Penalize high I/O wait
            iowait_penalty = min(iowait * 2, 20)

            return float(max(0, usage_score - iowait_penalty))
        except Exception:
            return 0.0

    @staticmethod
    def calculate_memory_score(memory_data: dict[str, Any]) -> float:
        """Calculate memory health score (0-100, higher is better)."""
        try:
            percent = memory_data.get("percent", 0)
            # Simple inverse of usage percentage
            return float(max(0, 100 - percent))
        except Exception:
            return 0.0

    @staticmethod
    def calculate_disk_score(disk_data: list[dict[str, Any]]) -> float:
        """Calculate disk health score (0-100, higher is better)."""
        if not disk_data:
            return 0.0

        try:
            total_score = 0
            count = 0

            for disk in disk_data:
                percent = disk.get("percent", 0)
                # Score based on available space
                disk_score = max(0, 100 - percent)
                total_score += disk_score
                count += 1

            return total_score / count if count > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def calculate_network_score(network_data: list[dict[str, Any]]) -> float:
        """Calculate network health score (0-100, higher is better)."""
        if not network_data:
            return 100.0  # No network data means no issues

        try:
            total_errors = 0
            total_packets = 0

            for interface in network_data:
                rx_errors = interface.get("rx_errors", 0)
                tx_errors = interface.get("tx_errors", 0)
                rx_packets = interface.get("rx_packets", 0)
                tx_packets = interface.get("tx_packets", 0)

                total_errors += rx_errors + tx_errors
                total_packets += rx_packets + tx_packets

            if total_packets == 0:
                return 100.0

            error_rate = (total_errors / total_packets) * 100
            return max(0, 100 - (error_rate * 10))  # Scale error impact
        except Exception:
            return 100.0

    @staticmethod
    def calculate_load_score(load_data: dict[str, Any], cpu_count: int = 1) -> float:
        """Calculate system load score (0-100, higher is better)."""
        try:
            load_1min = load_data.get("min1", 0)
            load_5min = load_data.get("min5", 0)
            load_15min = load_data.get("min15", 0)

            # Normalize by CPU count
            normalized_loads = [
                load_1min / cpu_count,
                load_5min / cpu_count,
                load_15min / cpu_count
            ]

            # Average normalized load
            avg_load = sum(normalized_loads) / len(normalized_loads)

            # Score based on load (1.0 is 100% CPU utilization)
            if avg_load <= 0.7:
                return 100.0
            elif avg_load <= 1.0:
                return float(100 - ((avg_load - 0.7) * 100))
            else:
                return float(max(0, 70 - (avg_load - 1.0) * 30))
        except Exception:
            return 0.0

    @staticmethod
    def calculate_composite_score(scores: dict[str, float], weights: dict[str, float] | None = None) -> float:
        """Calculate weighted composite score."""
        if not scores:
            return 0.0

        if weights is None:
            weights = {
                "cpu": 0.25,
                "memory": 0.25,
                "disk": 0.25,
                "network": 0.15,
                "load": 0.10
            }

        total_score = 0.0
        total_weight = 0.0

        for metric, score in scores.items():
            weight = weights.get(metric, 0.0)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def detect_anomalies(
        values: list[float],
        threshold_std: float = 2.0
    ) -> list[tuple[int, float, str]]:
        """Detect statistical anomalies in values."""
        if len(values) < 3:
            return []

        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)

            anomalies = []
            for i, value in enumerate(values):
                z_score = abs(value - mean) / stdev if stdev > 0 else 0

                if z_score > threshold_std:
                    anomaly_type = "high" if value > mean else "low"
                    anomalies.append((i, value, anomaly_type))

            return anomalies
        except Exception:
            return []

    @staticmethod
    def calculate_trend(
        points: list[MetricPoint],
        window_minutes: int = 30
    ) -> dict[str, Any]:
        """Calculate trend information for metric points."""
        if len(points) < 2:
            return {
                "direction": "stable",
                "slope": 0.0,
                "confidence": 0.0,
                "recent_change": 0.0
            }

        try:
            # Sort by timestamp
            sorted_points = sorted(points, key=lambda p: p.timestamp)

            # Filter to window
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            recent_points = [p for p in sorted_points if p.timestamp >= cutoff_time]

            if len(recent_points) < 2:
                recent_points = sorted_points[-2:]

            # Calculate linear regression
            x_values = [(p.timestamp - recent_points[0].timestamp).total_seconds()
                       for p in recent_points]
            y_values = [p.value for p in recent_points]

            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values, strict=False))
            sum_x2 = sum(x * x for x in x_values)

            # Calculate slope
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0

            # Determine direction
            if abs(slope) < 0.01:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"

            # Calculate confidence (correlation coefficient)
            try:
                correlation = statistics.correlation(x_values, y_values)
                confidence = abs(correlation)
            except (ValueError, ZeroDivisionError):
                confidence = 0.0

            # Recent change percentage
            if len(recent_points) >= 2:
                start_value = recent_points[0].value
                end_value = recent_points[-1].value
                recent_change = ((end_value - start_value) / start_value * 100) if start_value != 0 else 0.0
            else:
                recent_change = 0.0

            return {
                "direction": direction,
                "slope": slope,
                "confidence": confidence,
                "recent_change": recent_change
            }
        except Exception:
            return {
                "direction": "unknown",
                "slope": 0.0,
                "confidence": 0.0,
                "recent_change": 0.0
            }

    @staticmethod
    def calculate_baseline(
        points: list[MetricPoint],
        confidence_level: float = 0.95
    ) -> PerformanceBaseline:
        """Calculate performance baseline from historical data."""
        if not points:
            raise ValueError("No data points provided for baseline calculation")

        values = [p.value for p in points]

        # Calculate statistics
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0

        # Calculate confidence interval
        if len(values) > 1:
            # Using z-score for normal distribution approximation
            z_score = 1.96 if confidence_level == 0.95 else 2.58  # 99% confidence
            margin = z_score * (std_dev / (len(values) ** 0.5))
            confidence_interval = (mean_value - margin, mean_value + margin)
        else:
            confidence_interval = (mean_value, mean_value)

        # Determine validity period (e.g., 7 days from now)
        created_at = datetime.now()
        valid_until = created_at + timedelta(days=7)

        return PerformanceBaseline(
            server_alias=points[0].tags.get("server_alias", "unknown"),
            metric_name=points[0].tags.get("metric_name", "unknown"),
            baseline_value=mean_value,
            std_deviation=std_dev,
            confidence_interval=confidence_interval,
            sample_size=len(points),
            created_at=created_at,
            valid_until=valid_until
        )

    @staticmethod
    def compare_to_baseline(
        current_value: float,
        baseline: PerformanceBaseline,
        threshold_std: float = 2.0
    ) -> dict[str, Any]:
        """Compare current value to baseline."""
        if baseline.std_deviation == 0:
            deviation = 0.0
            z_score = 0.0
        else:
            deviation = current_value - baseline.baseline_value
            z_score = deviation / baseline.std_deviation

        # Determine status
        if abs(z_score) <= 1.0:
            status = "normal"
        elif abs(z_score) <= threshold_std:
            status = "warning"
        else:
            status = "critical"

        # Calculate percentage change
        if baseline.baseline_value != 0:
            percent_change = (deviation / baseline.baseline_value) * 100
        else:
            percent_change = 0.0

        return {
            "status": status,
            "current_value": current_value,
            "baseline_value": baseline.baseline_value,
            "deviation": deviation,
            "z_score": z_score,
            "percent_change": percent_change,
            "within_confidence_interval": baseline.confidence_interval[0] <= current_value <= baseline.confidence_interval[1]
        }
