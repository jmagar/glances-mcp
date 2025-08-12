"""Performance baseline management for Glances MCP server."""

import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any, cast

from glances_mcp.config.models import MetricPoint, PerformanceBaseline
from glances_mcp.config.settings import settings
from glances_mcp.services.glances_client import GlancesClientPool
from glances_mcp.utils.helpers import CircularBuffer
from glances_mcp.utils.logging import logger
from glances_mcp.utils.metrics import MetricsCalculator


class BaselineManager:
    """Manager for performance baselines and historical data."""

    def __init__(self, client_pool: GlancesClientPool):
        self.client_pool = client_pool
        self.metrics_calculator = MetricsCalculator()
        self.data_dir = Path("data/baselines")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for recent data points
        self.recent_data: dict[str, dict[str, CircularBuffer]] = {}

        # Cache for computed baselines
        self.baseline_cache: dict[str, PerformanceBaseline] = {}
        self.baseline_cache_ttl = 3600  # 1 hour

        # Metrics to collect for baselines
        self.baseline_metrics = [
            "cpu.total",
            "mem.percent",
            "load.min1",
            "load.min5",
            "load.min15"
        ]

    def _get_server_data_buffer(self, server_alias: str, metric: str) -> CircularBuffer:
        """Get or create data buffer for server metric."""
        if server_alias not in self.recent_data:
            self.recent_data[server_alias] = {}

        if metric not in self.recent_data[server_alias]:
            # Store last 24 hours of 5-minute samples
            buffer_size = 24 * 12  # 288 samples
            self.recent_data[server_alias][metric] = CircularBuffer(buffer_size)

        return self.recent_data[server_alias][metric]

    def _get_baseline_file_path(self, server_alias: str) -> Path:
        """Get file path for server baseline data."""
        return self.data_dir / f"{server_alias}_baselines.json"

    async def collect_metrics_sample(self, server_alias: str | None = None) -> None:
        """Collect a sample of metrics for baseline calculation."""
        servers_to_collect = (
            [server_alias] if server_alias
            else list(self.client_pool.get_enabled_clients().keys())
        )

        timestamp = datetime.now()

        for alias in servers_to_collect:
            client = self.client_pool.get_client(alias)
            if not client:
                continue

            try:
                # Collect basic system metrics
                cpu_data = await client.get_cpu_info()
                memory_data = await client.get_memory_info()
                load_data = await client.get_load_average()

                # Store metrics in buffers
                metrics_data = {
                    "cpu.total": cpu_data.get("total", 0),
                    "mem.percent": memory_data.get("percent", 0),
                    "load.min1": load_data.get("min1", 0),
                    "load.min5": load_data.get("min5", 0),
                    "load.min15": load_data.get("min15", 0)
                }

                for metric, value in metrics_data.items():
                    if value is not None:
                        buffer = self._get_server_data_buffer(alias, metric)

                        metric_point = MetricPoint(
                            timestamp=timestamp,
                            value=float(value),
                            tags={
                                "server_alias": alias,
                                "metric_name": metric
                            }
                        )

                        buffer.append(metric_point)

                logger.debug(
                    "Collected metrics sample for baseline",
                    server_alias=alias,
                    timestamp=timestamp.isoformat(),
                    metrics_count=len(metrics_data)
                )

            except Exception as e:
                logger.error(
                    "Error collecting metrics sample",
                    server_alias=alias,
                    error=str(e)
                )

    def calculate_baseline(
        self,
        server_alias: str,
        metric: str,
        hours: int = 24,
        confidence_level: float = 0.95
    ) -> PerformanceBaseline | None:
        """Calculate performance baseline for a metric."""
        buffer = self._get_server_data_buffer(server_alias, metric)

        # Get data points from the specified time window
        cutoff_time = datetime.now() - timedelta(hours=hours)
        all_points = buffer.get_all()

        recent_points = [
            point for point in all_points
            if isinstance(point, MetricPoint) and point.timestamp >= cutoff_time
        ]

        if len(recent_points) < 10:  # Need minimum data points
            logger.warning(
                "Insufficient data points for baseline calculation",
                server_alias=server_alias,
                metric=metric,
                points_available=len(recent_points),
                minimum_required=10
            )
            return None

        try:
            baseline = self.metrics_calculator.calculate_baseline(
                recent_points,
                confidence_level
            )

            # Update cache
            cache_key = f"{server_alias}:{metric}"
            self.baseline_cache[cache_key] = baseline

            logger.info(
                "Calculated performance baseline",
                server_alias=server_alias,
                metric=metric,
                baseline_value=baseline.baseline_value,
                std_deviation=baseline.std_deviation,
                sample_size=baseline.sample_size
            )

            return baseline

        except Exception as e:
            logger.error(
                "Error calculating baseline",
                server_alias=server_alias,
                metric=metric,
                error=str(e)
            )
            return None

    def get_cached_baseline(
        self,
        server_alias: str,
        metric: str,
        max_age_hours: int = 1
    ) -> PerformanceBaseline | None:
        """Get cached baseline if available and not expired."""
        cache_key = f"{server_alias}:{metric}"
        baseline = self.baseline_cache.get(cache_key)

        if not baseline:
            return None

        # Check if baseline is still valid
        age = (datetime.now() - baseline.created_at).total_seconds() / 3600

        if age > max_age_hours or datetime.now() > baseline.valid_until:
            # Remove expired baseline from cache
            del self.baseline_cache[cache_key]
            return None

        return baseline

    async def calculate_all_baselines(self, server_alias: str | None = None) -> dict[str, dict[str, PerformanceBaseline]]:
        """Calculate baselines for all metrics and servers."""
        results: dict[str, dict[str, PerformanceBaseline]] = {}

        servers = (
            [server_alias] if server_alias
            else list(self.client_pool.get_enabled_clients().keys())
        )

        for alias in servers:
            results[alias] = {}

            for metric in self.baseline_metrics:
                baseline = self.calculate_baseline(alias, metric)
                if baseline:
                    results[alias][metric] = baseline

        return results

    def compare_to_baseline(
        self,
        server_alias: str,
        metric: str,
        current_value: float,
        threshold_std: float = 2.0
    ) -> dict[str, Any] | None:
        """Compare current value to baseline."""
        # Try cached baseline first
        baseline = self.get_cached_baseline(server_alias, metric)

        if not baseline:
            # Calculate new baseline
            baseline = self.calculate_baseline(server_alias, metric)

            if not baseline:
                return None

        return self.metrics_calculator.compare_to_baseline(
            current_value,
            baseline,
            threshold_std
        )

    def get_trend_analysis(
        self,
        server_alias: str,
        metric: str,
        window_minutes: int = 60
    ) -> dict[str, Any] | None:
        """Get trend analysis for a metric."""
        buffer = self._get_server_data_buffer(server_alias, metric)

        # Get recent points
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        all_points = buffer.get_all()

        recent_points = [
            point for point in all_points
            if isinstance(point, MetricPoint) and point.timestamp >= cutoff_time
        ]

        if len(recent_points) < 2:
            return None

        return self.metrics_calculator.calculate_trend(recent_points, window_minutes)

    def save_baselines_to_disk(self, server_alias: str) -> None:
        """Save baselines to disk for persistence."""
        baselines_data = {}

        # Collect baselines for this server
        for metric in self.baseline_metrics:
            cache_key = f"{server_alias}:{metric}"
            if cache_key in self.baseline_cache:
                baseline = self.baseline_cache[cache_key]
                baselines_data[metric] = baseline.model_dump()

        if not baselines_data:
            return

        try:
            file_path = self._get_baseline_file_path(server_alias)
            with open(file_path, "w") as f:
                json.dump(baselines_data, f, indent=2, default=str)

            logger.info(
                "Saved baselines to disk",
                server_alias=server_alias,
                file_path=str(file_path),
                baselines_count=len(baselines_data)
            )

        except Exception as e:
            logger.error(
                "Error saving baselines to disk",
                server_alias=server_alias,
                error=str(e)
            )

    def load_baselines_from_disk(self, server_alias: str) -> None:
        """Load baselines from disk."""
        file_path = self._get_baseline_file_path(server_alias)

        if not file_path.exists():
            return

        try:
            with open(file_path) as f:
                baselines_data = json.load(f)

            loaded_count = 0
            for metric, baseline_dict in baselines_data.items():
                try:
                    baseline = PerformanceBaseline.model_validate(baseline_dict)

                    # Only load if still valid
                    if datetime.now() <= baseline.valid_until:
                        cache_key = f"{server_alias}:{metric}"
                        self.baseline_cache[cache_key] = baseline
                        loaded_count += 1

                except Exception as e:
                    logger.warning(
                        "Error loading baseline",
                        server_alias=server_alias,
                        metric=metric,
                        error=str(e)
                    )

            logger.info(
                "Loaded baselines from disk",
                server_alias=server_alias,
                loaded_count=loaded_count,
                total_found=len(baselines_data)
            )

        except Exception as e:
            logger.error(
                "Error loading baselines from disk",
                server_alias=server_alias,
                error=str(e)
            )

    def get_baseline_summary(self) -> dict[str, Any]:
        """Get summary of available baselines."""
        summary: dict[str, Any] = {
            "total_baselines": len(self.baseline_cache),
            "servers_with_baselines": len({
                key.split(":")[0] for key in self.baseline_cache.keys()
            }),
            "metrics_tracked": list(self.baseline_metrics),
            "oldest_baseline": None,
            "newest_baseline": None,
            "baselines_by_server": cast(dict[str, int], {})
        }

        if self.baseline_cache:
            baselines = list(self.baseline_cache.values())
            sorted_baselines = sorted(baselines, key=lambda b: b.created_at)

            summary["oldest_baseline"] = sorted_baselines[0].created_at.isoformat()
            summary["newest_baseline"] = sorted_baselines[-1].created_at.isoformat()

            # Count by server
            for cache_key in self.baseline_cache.keys():
                server_alias = cache_key.split(":")[0]
                if server_alias not in summary["baselines_by_server"]:
                    summary["baselines_by_server"][server_alias] = 0
                summary["baselines_by_server"][server_alias] += 1

        return summary

    async def cleanup_old_data(self) -> None:
        """Clean up old baseline data."""
        retention_days = settings.baseline_retention_days
        cutoff_time = datetime.now() - timedelta(days=retention_days)

        # Clean up cache
        expired_keys = []
        for cache_key, baseline in self.baseline_cache.items():
            if baseline.created_at < cutoff_time or datetime.now() > baseline.valid_until:
                expired_keys.append(cache_key)

        for key in expired_keys:
            del self.baseline_cache[key]

        logger.info(
            "Cleaned up expired baselines",
            expired_count=len(expired_keys),
            retention_days=retention_days
        )

    async def run_baseline_collection(self, interval_minutes: int = 5) -> None:
        """Run continuous baseline data collection."""
        logger.info(
            "Starting baseline data collection",
            interval_minutes=interval_minutes
        )

        # Load existing baselines on startup
        for server_alias in self.client_pool.servers.keys():
            self.load_baselines_from_disk(server_alias)

        while True:
            try:
                # Collect metrics samples
                await self.collect_metrics_sample()

                # Calculate new baselines every hour
                current_time = datetime.now()
                if current_time.minute == 0:
                    await self.calculate_all_baselines()

                    # Save baselines to disk
                    for server_alias in self.client_pool.servers.keys():
                        self.save_baselines_to_disk(server_alias)

                    # Cleanup old data
                    await self.cleanup_old_data()

            except Exception as e:
                logger.error("Error during baseline collection", error=str(e))

            await asyncio.sleep(interval_minutes * 60)
