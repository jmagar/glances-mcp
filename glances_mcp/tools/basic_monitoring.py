"""Basic monitoring tools for Glances MCP server."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from config.validation import InputValidator
from glances_mcp.services.glances_client import GlancesClientPool, GlancesApiError
from glances_mcp.utils.helpers import format_bytes, format_percentage, format_uptime, safe_get
from glances_mcp.utils.logging import logger, performance_logger


def register_basic_monitoring_tools(app: FastMCP, client_pool: GlancesClientPool) -> None:
    """Register basic monitoring tools with the MCP server."""
    
    @app.tool()
    async def list_servers() -> Dict[str, Any]:
        """List all configured Glances servers with their status and capabilities."""
        start_time = datetime.now()
        
        try:
            # Get health status for all servers
            health_statuses = await client_pool.health_check_all()
            
            servers_info = []
            for alias, server_config in client_pool.servers.items():
                server_status = health_statuses.get(alias)
                
                server_info = {
                    "alias": server_config.alias,
                    "host": server_config.host,
                    "port": server_config.port,
                    "protocol": server_config.protocol,
                    "environment": server_config.environment.value if server_config.environment else None,
                    "region": server_config.region,
                    "tags": server_config.tags,
                    "enabled": server_config.enabled,
                    "status": {
                        "health": server_status.health.status if server_status else "unknown",
                        "message": server_status.health.message if server_status else "No status available",
                        "last_check": server_status.health.timestamp.isoformat() if server_status else None,
                        "response_time_ms": server_status.response_time_ms if server_status else None,
                        "glances_version": server_status.glances_version if server_status else None,
                        "capabilities": server_status.capabilities if server_status else []
                    }
                }
                servers_info.append(server_info)
            
            # Sort by health status (healthy first, then by alias)
            servers_info.sort(key=lambda s: (
                {"healthy": 0, "warning": 1, "degraded": 2, "critical": 3, "unknown": 4}.get(s["status"]["health"], 5),
                s["alias"]
            ))
            
            result = {
                "servers": servers_info,
                "summary": {
                    "total_servers": len(servers_info),
                    "enabled_servers": len([s for s in servers_info if s["enabled"]]),
                    "healthy_servers": len([s for s in servers_info if s["status"]["health"] == "healthy"]),
                    "servers_with_issues": len([s for s in servers_info if s["status"]["health"] in ["warning", "critical"]]),
                    "environments": list(set(s["environment"] for s in servers_info if s["environment"])),
                    "regions": list(set(s["region"] for s in servers_info if s["region"]))
                }
            }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("list_servers", duration_ms, True)
            
            return result
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("list_servers", duration_ms, False)
            logger.error("Error in list_servers", error=str(e))
            raise
    
    @app.tool()
    async def get_server_status(server_alias: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed status information for one or all servers."""
        start_time = datetime.now()
        
        try:
            if server_alias:
                # Validate server alias
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                
                client = client_pool.get_client(server_alias)
                if not client:
                    raise ValueError(f"Client for server '{server_alias}' not available")
                
                server_status = await client.health_check()
                servers_status = {server_alias: server_status}
            else:
                servers_status = await client_pool.health_check_all()
            
            detailed_status = {}
            for alias, status in servers_status.items():
                detailed_status[alias] = {
                    "health": status.health.status,
                    "message": status.health.message,
                    "timestamp": status.health.timestamp.isoformat(),
                    "last_successful_connection": (
                        status.last_successful_connection.isoformat() 
                        if status.last_successful_connection else None
                    ),
                    "response_time_ms": status.response_time_ms,
                    "glances_version": status.glances_version,
                    "capabilities": status.capabilities,
                    "server_config": {
                        "host": client_pool.servers[alias].host,
                        "port": client_pool.servers[alias].port,
                        "environment": (
                            client_pool.servers[alias].environment.value 
                            if client_pool.servers[alias].environment else None
                        ),
                        "region": client_pool.servers[alias].region,
                        "tags": client_pool.servers[alias].tags
                    }
                }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_server_status", duration_ms, True)
            
            return {"servers": detailed_status}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_server_status", duration_ms, False)
            logger.error("Error in get_server_status", server_alias=server_alias, error=str(e))
            raise
    
    @app.tool()
    async def get_system_overview(server_alias: Optional[str] = None) -> Dict[str, Any]:
        """Get system overview including CPU, memory, load, and uptime for one or all servers."""
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
            
            systems_overview = {}
            
            for alias, client in clients.items():
                try:
                    # Get core system metrics
                    system_data = await client.get_system_info()
                    cpu_data = await client.get_cpu_info()
                    memory_data = await client.get_memory_info()
                    load_data = await client.get_load_average()
                    uptime_data = await client.get_uptime()
                    
                    overview = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "system": {
                            "hostname": safe_get(system_data, "hostname", "unknown"),
                            "platform": safe_get(system_data, "platform", "unknown"),
                            "linux_distro": safe_get(system_data, "linux_distro", "unknown"),
                            "hr_name": safe_get(system_data, "hr_name", "unknown")
                        },
                        "cpu": {
                            "count": safe_get(system_data, "cpucount", 1),
                            "total_usage": safe_get(cpu_data, "total", 0),
                            "user": safe_get(cpu_data, "user", 0),
                            "system": safe_get(cpu_data, "system", 0),
                            "iowait": safe_get(cpu_data, "iowait", 0),
                            "usage_formatted": format_percentage(safe_get(cpu_data, "total", 0))
                        },
                        "memory": {
                            "total": safe_get(memory_data, "total", 0),
                            "available": safe_get(memory_data, "available", 0),
                            "used": safe_get(memory_data, "used", 0),
                            "percent": safe_get(memory_data, "percent", 0),
                            "total_formatted": format_bytes(safe_get(memory_data, "total", 0)),
                            "available_formatted": format_bytes(safe_get(memory_data, "available", 0)),
                            "usage_formatted": format_percentage(safe_get(memory_data, "percent", 0))
                        },
                        "load": {
                            "min1": safe_get(load_data, "min1", 0),
                            "min5": safe_get(load_data, "min5", 0),
                            "min15": safe_get(load_data, "min15", 0),
                            "cpucore": safe_get(load_data, "cpucore", 1)
                        },
                        "uptime": {
                            "seconds": safe_get(uptime_data, "seconds", 0),
                            "formatted": format_uptime(safe_get(uptime_data, "seconds", 0))
                        }
                    }
                    
                    systems_overview[alias] = overview
                
                except GlancesApiError as e:
                    logger.warning(
                        "Error getting system overview for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    systems_overview[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_system_overview", duration_ms, True)
            
            return {"systems": systems_overview}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_system_overview", duration_ms, False)
            logger.error("Error in get_system_overview", server_alias=server_alias, error=str(e))
            raise
    
    @app.tool()
    async def get_detailed_metrics(
        server_alias: Optional[str] = None,
        include_sensors: bool = False
    ) -> Dict[str, Any]:
        """Get detailed system metrics including extended CPU, memory, and I/O statistics."""
        start_time = datetime.now()
        
        try:
            # Validate parameters
            validated_params = InputValidator.validate_tool_params(
                "get_detailed_metrics",
                {"server_alias": server_alias, "include_sensors": include_sensors}
            )
            
            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()
            
            detailed_metrics = {}
            
            for alias, client in clients.items():
                try:
                    # Get detailed metrics
                    cpu_data = await client.get_cpu_info()
                    memory_data = await client.get_memory_info()
                    disk_io_data = await client.get_disk_io()
                    
                    metrics = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "cpu_detailed": {
                            "total": safe_get(cpu_data, "total", 0),
                            "user": safe_get(cpu_data, "user", 0),
                            "nice": safe_get(cpu_data, "nice", 0),
                            "system": safe_get(cpu_data, "system", 0),
                            "idle": safe_get(cpu_data, "idle", 0),
                            "iowait": safe_get(cpu_data, "iowait", 0),
                            "irq": safe_get(cpu_data, "irq", 0),
                            "softirq": safe_get(cpu_data, "softirq", 0),
                            "steal": safe_get(cpu_data, "steal", 0),
                            "guest": safe_get(cpu_data, "guest", 0),
                            "guest_nice": safe_get(cpu_data, "guest_nice", 0)
                        },
                        "memory_detailed": {
                            "total": safe_get(memory_data, "total", 0),
                            "available": safe_get(memory_data, "available", 0),
                            "percent": safe_get(memory_data, "percent", 0),
                            "used": safe_get(memory_data, "used", 0),
                            "free": safe_get(memory_data, "free", 0),
                            "active": safe_get(memory_data, "active", 0),
                            "inactive": safe_get(memory_data, "inactive", 0),
                            "buffers": safe_get(memory_data, "buffers", 0),
                            "cached": safe_get(memory_data, "cached", 0),
                            "shared": safe_get(memory_data, "shared", 0),
                            "slab": safe_get(memory_data, "slab", 0)
                        }
                    }
                    
                    # Add disk I/O statistics
                    if disk_io_data:
                        io_stats = []
                        for disk in disk_io_data:
                            io_stat = {
                                "disk_name": safe_get(disk, "disk_name", "unknown"),
                                "read_count": safe_get(disk, "read_count", 0),
                                "write_count": safe_get(disk, "write_count", 0),
                                "read_bytes": safe_get(disk, "read_bytes", 0),
                                "write_bytes": safe_get(disk, "write_bytes", 0),
                                "read_time": safe_get(disk, "read_time", 0),
                                "write_time": safe_get(disk, "write_time", 0),
                                "read_bytes_formatted": format_bytes(safe_get(disk, "read_bytes", 0)),
                                "write_bytes_formatted": format_bytes(safe_get(disk, "write_bytes", 0))
                            }
                            io_stats.append(io_stat)
                        metrics["disk_io"] = io_stats
                    
                    # Add sensor data if requested and available
                    if include_sensors:
                        try:
                            sensors_data = await client.get_sensors()
                            if sensors_data:
                                metrics["sensors"] = sensors_data
                        except:
                            pass  # Sensors might not be available
                    
                    detailed_metrics[alias] = metrics
                
                except GlancesApiError as e:
                    logger.warning(
                        "Error getting detailed metrics for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    detailed_metrics[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_detailed_metrics", duration_ms, True)
            
            return {"servers": detailed_metrics}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_detailed_metrics", duration_ms, False)
            logger.error("Error in get_detailed_metrics", server_alias=server_alias, error=str(e))
            raise
    
    @app.tool()
    async def get_disk_usage(server_alias: Optional[str] = None) -> Dict[str, Any]:
        """Get disk usage information for all mount points."""
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
            
            servers_disk_usage = {}
            
            for alias, client in clients.items():
                try:
                    disk_data = await client.get_disk_usage()
                    
                    filesystems = []
                    total_size = 0
                    total_used = 0
                    total_free = 0
                    
                    for fs in disk_data:
                        filesystem = {
                            "device_name": safe_get(fs, "device_name", "unknown"),
                            "mnt_point": safe_get(fs, "mnt_point", "unknown"),
                            "fs_type": safe_get(fs, "fs_type", "unknown"),
                            "size": safe_get(fs, "size", 0),
                            "used": safe_get(fs, "used", 0),
                            "free": safe_get(fs, "free", 0),
                            "percent": safe_get(fs, "percent", 0),
                            "size_formatted": format_bytes(safe_get(fs, "size", 0)),
                            "used_formatted": format_bytes(safe_get(fs, "used", 0)),
                            "free_formatted": format_bytes(safe_get(fs, "free", 0)),
                            "usage_formatted": format_percentage(safe_get(fs, "percent", 0))
                        }
                        filesystems.append(filesystem)
                        
                        # Aggregate totals (excluding special filesystems)
                        if not safe_get(fs, "mnt_point", "").startswith(("/dev", "/proc", "/sys", "/run")):
                            total_size += safe_get(fs, "size", 0)
                            total_used += safe_get(fs, "used", 0)
                            total_free += safe_get(fs, "free", 0)
                    
                    # Sort by mount point
                    filesystems.sort(key=lambda x: x["mnt_point"])
                    
                    usage_summary = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "filesystems": filesystems,
                        "summary": {
                            "filesystem_count": len(filesystems),
                            "total_size": total_size,
                            "total_used": total_used,
                            "total_free": total_free,
                            "total_percent": (total_used / total_size * 100) if total_size > 0 else 0,
                            "total_size_formatted": format_bytes(total_size),
                            "total_used_formatted": format_bytes(total_used),
                            "total_free_formatted": format_bytes(total_free),
                            "critical_filesystems": [
                                fs for fs in filesystems 
                                if fs["percent"] >= 95
                            ],
                            "warning_filesystems": [
                                fs for fs in filesystems 
                                if 85 <= fs["percent"] < 95
                            ]
                        }
                    }
                    
                    servers_disk_usage[alias] = usage_summary
                
                except GlancesApiError as e:
                    logger.warning(
                        "Error getting disk usage for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    servers_disk_usage[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_disk_usage", duration_ms, True)
            
            return {"servers": servers_disk_usage}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_disk_usage", duration_ms, False)
            logger.error("Error in get_disk_usage", server_alias=server_alias, error=str(e))
            raise
    
    @app.tool()
    async def get_network_stats(server_alias: Optional[str] = None) -> Dict[str, Any]:
        """Get network interface statistics and traffic information."""
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
            
            servers_network_stats = {}
            
            for alias, client in clients.items():
                try:
                    network_data = await client.get_network_interfaces()
                    
                    interfaces = []
                    total_rx_bytes = 0
                    total_tx_bytes = 0
                    total_rx_packets = 0
                    total_tx_packets = 0
                    total_errors = 0
                    
                    for interface in network_data:
                        interface_name = safe_get(interface, "interface_name", "unknown")
                        
                        # Skip loopback and other special interfaces for totals
                        is_physical = not interface_name.startswith(("lo", "docker", "veth", "br-"))
                        
                        rx_bytes = safe_get(interface, "rx_bytes", 0)
                        tx_bytes = safe_get(interface, "tx_bytes", 0)
                        rx_packets = safe_get(interface, "rx_packets", 0)
                        tx_packets = safe_get(interface, "tx_packets", 0)
                        rx_errors = safe_get(interface, "rx_errors", 0)
                        tx_errors = safe_get(interface, "tx_errors", 0)
                        
                        interface_info = {
                            "interface_name": interface_name,
                            "rx_bytes": rx_bytes,
                            "tx_bytes": tx_bytes,
                            "rx_packets": rx_packets,
                            "tx_packets": tx_packets,
                            "rx_errors": rx_errors,
                            "tx_errors": tx_errors,
                            "rx_dropped": safe_get(interface, "rx_dropped", 0),
                            "tx_dropped": safe_get(interface, "tx_dropped", 0),
                            "rx_bytes_formatted": format_bytes(rx_bytes),
                            "tx_bytes_formatted": format_bytes(tx_bytes),
                            "error_rate": (
                                ((rx_errors + tx_errors) / (rx_packets + tx_packets) * 100)
                                if (rx_packets + tx_packets) > 0 else 0
                            ),
                            "is_physical": is_physical
                        }
                        interfaces.append(interface_info)
                        
                        if is_physical:
                            total_rx_bytes += rx_bytes
                            total_tx_bytes += tx_bytes
                            total_rx_packets += rx_packets
                            total_tx_packets += tx_packets
                            total_errors += rx_errors + tx_errors
                    
                    # Sort interfaces by name
                    interfaces.sort(key=lambda x: x["interface_name"])
                    
                    network_summary = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "interfaces": interfaces,
                        "summary": {
                            "interface_count": len(interfaces),
                            "physical_interfaces": len([i for i in interfaces if i["is_physical"]]),
                            "total_rx_bytes": total_rx_bytes,
                            "total_tx_bytes": total_tx_bytes,
                            "total_rx_packets": total_rx_packets,
                            "total_tx_packets": total_tx_packets,
                            "total_errors": total_errors,
                            "total_rx_formatted": format_bytes(total_rx_bytes),
                            "total_tx_formatted": format_bytes(total_tx_bytes),
                            "overall_error_rate": (
                                (total_errors / (total_rx_packets + total_tx_packets) * 100)
                                if (total_rx_packets + total_tx_packets) > 0 else 0
                            ),
                            "interfaces_with_errors": [
                                i["interface_name"] for i in interfaces 
                                if i["rx_errors"] > 0 or i["tx_errors"] > 0
                            ]
                        }
                    }
                    
                    servers_network_stats[alias] = network_summary
                
                except GlancesApiError as e:
                    logger.warning(
                        "Error getting network stats for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    servers_network_stats[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_network_stats", duration_ms, True)
            
            return {"servers": servers_network_stats}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_network_stats", duration_ms, False)
            logger.error("Error in get_network_stats", server_alias=server_alias, error=str(e))
            raise
    
    @app.tool()
    async def get_top_processes(
        server_alias: Optional[str] = None,
        limit: int = 10,
        sort_by: str = "cpu",
        filter_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get top processes sorted by CPU or memory usage."""
        start_time = datetime.now()
        
        try:
            # Validate parameters
            validated_params = InputValidator.validate_tool_params(
                "get_top_processes",
                {
                    "server_alias": server_alias,
                    "limit": limit,
                    "sort_by": sort_by,
                    "filter_name": filter_name
                }
            )
            
            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()
            
            servers_processes = {}
            
            for alias, client in clients.items():
                try:
                    processes_data = await client.get_processes()
                    
                    if not processes_data:
                        servers_processes[alias] = {
                            "server_alias": alias,
                            "error": "No process data available",
                            "timestamp": datetime.now().isoformat()
                        }
                        continue
                    
                    # Filter processes if requested
                    if filter_name:
                        processes_data = [
                            proc for proc in processes_data
                            if filter_name.lower() in safe_get(proc, "name", "").lower()
                        ]
                    
                    # Sort processes
                    sort_key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
                    processes_data.sort(
                        key=lambda p: safe_get(p, sort_key, 0),
                        reverse=True
                    )
                    
                    # Limit results
                    top_processes = processes_data[:limit]
                    
                    # Format process information
                    formatted_processes = []
                    for proc in top_processes:
                        process_info = {
                            "pid": safe_get(proc, "pid", 0),
                            "name": safe_get(proc, "name", "unknown"),
                            "username": safe_get(proc, "username", "unknown"),
                            "cpu_percent": safe_get(proc, "cpu_percent", 0),
                            "memory_percent": safe_get(proc, "memory_percent", 0),
                            "memory_info": safe_get(proc, "memory_info", {}),
                            "memory_rss": safe_get(proc, "memory_info", {}).get("rss", 0),
                            "memory_vms": safe_get(proc, "memory_info", {}).get("vms", 0),
                            "status": safe_get(proc, "status", "unknown"),
                            "create_time": safe_get(proc, "create_time", 0),
                            "num_threads": safe_get(proc, "num_threads", 0),
                            "nice": safe_get(proc, "nice", 0),
                            "memory_rss_formatted": format_bytes(
                                safe_get(proc, "memory_info", {}).get("rss", 0)
                            ),
                            "memory_vms_formatted": format_bytes(
                                safe_get(proc, "memory_info", {}).get("vms", 0)
                            ),
                            "cpu_times": safe_get(proc, "cpu_times", {})
                        }
                        
                        # Add command line (truncated for security)
                        cmdline = safe_get(proc, "cmdline", [])
                        if cmdline:
                            command_str = " ".join(cmdline)
                            # Truncate very long command lines
                            if len(command_str) > 100:
                                command_str = command_str[:97] + "..."
                            process_info["cmdline"] = command_str
                        else:
                            process_info["cmdline"] = safe_get(proc, "name", "unknown")
                        
                        formatted_processes.append(process_info)
                    
                    # Calculate summary statistics
                    total_cpu = sum(safe_get(p, "cpu_percent", 0) for p in processes_data)
                    total_memory = sum(safe_get(p, "memory_percent", 0) for p in processes_data)
                    
                    process_summary = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "processes": formatted_processes,
                        "summary": {
                            "total_processes": len(processes_data),
                            "displayed_processes": len(formatted_processes),
                            "sorted_by": sort_by,
                            "filter_applied": filter_name,
                            "top_processes_cpu_total": sum(
                                p["cpu_percent"] for p in formatted_processes
                            ),
                            "top_processes_memory_total": sum(
                                p["memory_percent"] for p in formatted_processes
                            ),
                            "running_processes": len([
                                p for p in processes_data 
                                if safe_get(p, "status") == "running"
                            ]),
                            "sleeping_processes": len([
                                p for p in processes_data 
                                if safe_get(p, "status") == "sleeping"
                            ])
                        }
                    }
                    
                    servers_processes[alias] = process_summary
                
                except GlancesApiError as e:
                    logger.warning(
                        "Error getting processes for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    servers_processes[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_top_processes", duration_ms, True)
            
            return {"servers": servers_processes}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_top_processes", duration_ms, False)
            logger.error("Error in get_top_processes", server_alias=server_alias, error=str(e))
            raise
    
    @app.tool()
    async def get_containers(
        server_alias: Optional[str] = None,
        include_stopped: bool = False
    ) -> Dict[str, Any]:
        """Get Docker/Podman container information and statistics."""
        start_time = datetime.now()
        
        try:
            # Validate parameters
            validated_params = InputValidator.validate_tool_params(
                "get_containers",
                {
                    "server_alias": server_alias,
                    "include_stopped": include_stopped
                }
            )
            
            clients = {}
            if server_alias:
                if server_alias not in client_pool.servers:
                    raise ValueError(f"Server '{server_alias}' not found")
                client = client_pool.get_client(server_alias)
                if client:
                    clients[server_alias] = client
            else:
                clients = client_pool.get_enabled_clients()
            
            servers_containers = {}
            
            for alias, client in clients.items():
                try:
                    containers_data = await client.get_containers()
                    
                    if not containers_data:
                        servers_containers[alias] = {
                            "server_alias": alias,
                            "containers": [],
                            "summary": {
                                "total_containers": 0,
                                "running_containers": 0,
                                "stopped_containers": 0,
                                "containers_available": False
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        continue
                    
                    # Filter containers by status if requested
                    if not include_stopped:
                        containers_data = [
                            container for container in containers_data
                            if safe_get(container, "Status", "").startswith("Up")
                        ]
                    
                    # Format container information
                    formatted_containers = []
                    running_count = 0
                    stopped_count = 0
                    
                    for container in containers_data:
                        status = safe_get(container, "Status", "unknown")
                        is_running = status.startswith("Up")
                        
                        if is_running:
                            running_count += 1
                        else:
                            stopped_count += 1
                        
                        container_info = {
                            "id": safe_get(container, "Id", "unknown")[:12],  # Short ID
                            "name": safe_get(container, "name", "unknown"),
                            "image": safe_get(container, "image", "unknown"),
                            "status": status,
                            "is_running": is_running,
                            "created": safe_get(container, "created", "unknown"),
                            "cpu_percent": safe_get(container, "cpu_percent", 0),
                            "memory_usage": safe_get(container, "memory_usage", 0),
                            "memory_limit": safe_get(container, "memory_limit", 0),
                            "memory_percent": safe_get(container, "memory_percent", 0),
                            "network_rx": safe_get(container, "network_rx", 0),
                            "network_tx": safe_get(container, "network_tx", 0),
                            "io_r": safe_get(container, "io_r", 0),
                            "io_w": safe_get(container, "io_w", 0),
                            "memory_usage_formatted": format_bytes(
                                safe_get(container, "memory_usage", 0)
                            ),
                            "memory_limit_formatted": format_bytes(
                                safe_get(container, "memory_limit", 0)
                            ),
                            "network_rx_formatted": format_bytes(
                                safe_get(container, "network_rx", 0)
                            ),
                            "network_tx_formatted": format_bytes(
                                safe_get(container, "network_tx", 0)
                            )
                        }
                        
                        formatted_containers.append(container_info)
                    
                    # Sort by CPU usage (descending)
                    formatted_containers.sort(
                        key=lambda c: c["cpu_percent"],
                        reverse=True
                    )
                    
                    container_summary = {
                        "server_alias": alias,
                        "timestamp": datetime.now().isoformat(),
                        "containers": formatted_containers,
                        "summary": {
                            "total_containers": len(containers_data),
                            "running_containers": running_count,
                            "stopped_containers": stopped_count,
                            "displayed_containers": len(formatted_containers),
                            "include_stopped": include_stopped,
                            "containers_available": True,
                            "total_cpu_usage": sum(
                                c["cpu_percent"] for c in formatted_containers
                            ),
                            "total_memory_usage": sum(
                                c["memory_usage"] for c in formatted_containers
                            ),
                            "total_memory_usage_formatted": format_bytes(
                                sum(c["memory_usage"] for c in formatted_containers)
                            )
                        }
                    }
                    
                    servers_containers[alias] = container_summary
                
                except GlancesApiError as e:
                    logger.warning(
                        "Error getting containers for server",
                        server_alias=alias,
                        error=str(e)
                    )
                    servers_containers[alias] = {
                        "server_alias": alias,
                        "error": str(e),
                        "containers": [],
                        "summary": {
                            "containers_available": False
                        },
                        "timestamp": datetime.now().isoformat()
                    }
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_containers", duration_ms, True)
            
            return {"servers": servers_containers}
        
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            performance_logger.log_tool_execution("get_containers", duration_ms, False)
            logger.error("Error in get_containers", server_alias=server_alias, error=str(e))
            raise