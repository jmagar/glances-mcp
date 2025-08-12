"""Helper utilities for Glances MCP server."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format."""
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format a percentage value."""
    return f"{value:.{decimal_places}f}%"


def format_uptime(seconds: int) -> str:
    """Format uptime seconds into human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def format_rate(value: float, unit: str = "B/s") -> str:
    """Format a rate value (e.g., bytes per second)."""
    if unit == "B/s":
        return format_bytes(int(value)) + "/s"
    else:
        return f"{value:.1f} {unit}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary using dot notation."""
    keys = path.split(".")
    current = data
    
    try:
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            else:
                return default
        return current
    except (KeyError, TypeError):
        return default


def calculate_average(values: List[float]) -> float:
    """Calculate average of a list of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = (percentile / 100) * (len(sorted_values) - 1)
    
    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def is_within_maintenance_window(
    maintenance_windows: List[Dict[str, Any]],
    current_time: Optional[datetime] = None
) -> bool:
    """Check if current time is within any maintenance window."""
    if not maintenance_windows:
        return False
    
    if current_time is None:
        current_time = datetime.now()
    
    # For simplicity, assume all times are in the same timezone
    current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday
    current_time_str = current_time.strftime("%H:%M")
    
    for window in maintenance_windows:
        if current_weekday in window.get("days_of_week", []):
            start_time = window.get("start_time", "00:00")
            end_time = window.get("end_time", "23:59")
            
            if start_time <= current_time_str <= end_time:
                return True
    
    return False


def generate_correlation_id() -> str:
    """Generate a correlation ID for request tracking."""
    import uuid
    return str(uuid.uuid4())[:8]


def merge_metrics(metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple metric dictionaries, aggregating numeric values."""
    if not metrics_list:
        return {}
    
    merged = {}
    
    for metrics in metrics_list:
        for key, value in metrics.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, (int, float)) and isinstance(merged[key], (int, float)):
                merged[key] += value
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key].extend(value)
    
    return merged


def filter_sensitive_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from data."""
    sensitive_keys = ["password", "token", "key", "secret", "credential"]
    
    filtered = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered[key] = "***REDACTED***"
        elif isinstance(value, dict):
            filtered[key] = filter_sensitive_info(value)
        else:
            filtered[key] = value
    
    return filtered


async def async_timeout(coro, timeout_seconds: float):
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")


def validate_json_serializable(data: Any) -> Any:
    """Validate that data is JSON serializable, converting if necessary."""
    try:
        json.dumps(data, default=str)
        return data
    except (TypeError, ValueError) as e:
        # Convert problematic types to strings
        if isinstance(data, dict):
            return {k: validate_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [validate_json_serializable(item) for item in data]
        elif isinstance(data, (datetime, timedelta)):
            return str(data)
        else:
            return str(data)


class CircularBuffer:
    """Simple circular buffer for storing recent values."""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer: List[Any] = []
        self.index = 0
    
    def append(self, value: Any) -> None:
        """Add value to buffer."""
        if len(self.buffer) < self.max_size:
            self.buffer.append(value)
        else:
            self.buffer[self.index] = value
            self.index = (self.index + 1) % self.max_size
    
    def get_all(self) -> List[Any]:
        """Get all values in chronological order."""
        if len(self.buffer) < self.max_size:
            return self.buffer.copy()
        else:
            return self.buffer[self.index:] + self.buffer[:self.index]
    
    def get_recent(self, count: int) -> List[Any]:
        """Get most recent N values."""
        all_values = self.get_all()
        return all_values[-count:] if count < len(all_values) else all_values


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []
    
    def can_make_call(self) -> bool:
        """Check if a call can be made within rate limits."""
        now = datetime.now().timestamp()
        
        # Remove calls outside the time window
        cutoff = now - self.time_window
        self.calls = [call_time for call_time in self.calls if call_time > cutoff]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self) -> None:
        """Record that a call was made."""
        self.calls.append(datetime.now().timestamp())