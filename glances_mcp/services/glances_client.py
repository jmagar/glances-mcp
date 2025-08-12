"""Glances API client for the MCP server."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from config.models import GlancesServer, ServerStatus, HealthStatus
from glances_mcp.utils.helpers import async_timeout, generate_correlation_id, RateLimiter
from glances_mcp.utils.logging import logger, performance_logger


class GlancesApiError(Exception):
    """Custom exception for Glances API errors."""
    
    def __init__(self, message: str, server_alias: str, status_code: Optional[int] = None):
        self.message = message
        self.server_alias = server_alias
        self.status_code = status_code
        super().__init__(f"[{server_alias}] {message}")


class GlancesClient:
    """Async client for Glances API."""
    
    def __init__(self, server: GlancesServer):
        self.server = server
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(max_calls=60, time_window=60)  # 60 calls per minute
        self._last_health_check: Optional[datetime] = None
        self._cached_version: Optional[str] = None
        self._cached_capabilities: List[str] = []
    
    async def __aenter__(self) -> "GlancesClient":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def connect(self) -> None:
        """Initialize the HTTP session."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.server.timeout)
            auth = None
            
            if self.server.username and self.server.password:
                auth = aiohttp.BasicAuth(self.server.username, self.server.password)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                auth=auth
            )
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, endpoint: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Make an HTTP request to Glances API."""
        if correlation_id is None:
            correlation_id = generate_correlation_id()
        
        if not self.rate_limiter.can_make_call():
            raise GlancesApiError("Rate limit exceeded", self.server.alias)
        
        url = f"{self.server.base_url}/api/3/{endpoint}"
        start_time = datetime.now()
        
        try:
            if not self.session:
                await self.connect()
            
            async with self.session.get(url) as response:
                response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                self.rate_limiter.record_call()
                
                performance_logger.log_server_response_time(
                    server_alias=self.server.alias,
                    endpoint=endpoint,
                    response_time_ms=response_time_ms,
                    success=response.status == 200
                )
                
                if response.status == 200:
                    data = await response.json()
                    logger.debug(
                        "Glances API request successful",
                        server_alias=self.server.alias,
                        endpoint=endpoint,
                        correlation_id=correlation_id,
                        response_time_ms=response_time_ms
                    )
                    return data
                elif response.status == 401:
                    raise GlancesApiError("Authentication failed", self.server.alias, 401)
                elif response.status == 404:
                    raise GlancesApiError(f"Endpoint not found: {endpoint}", self.server.alias, 404)
                else:
                    error_text = await response.text()
                    raise GlancesApiError(
                        f"HTTP {response.status}: {error_text}",
                        self.server.alias,
                        response.status
                    )
        
        except aiohttp.ClientTimeout:
            raise GlancesApiError("Request timeout", self.server.alias)
        except aiohttp.ClientConnectionError:
            raise GlancesApiError("Connection error", self.server.alias)
        except Exception as e:
            if isinstance(e, GlancesApiError):
                raise
            raise GlancesApiError(f"Unexpected error: {str(e)}", self.server.alias)
    
    async def health_check(self) -> ServerStatus:
        """Perform health check on the Glances server."""
        start_time = datetime.now()
        
        try:
            # Try to get basic system info
            await self._make_request("system")
            
            response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get version and capabilities if not cached
            if self._cached_version is None:
                try:
                    version_data = await self._make_request("version")
                    self._cached_version = version_data.get("version", "unknown")
                except:
                    self._cached_version = "unknown"
            
            if not self._cached_capabilities:
                try:
                    # Get available endpoints to determine capabilities
                    await self._discover_capabilities()
                except:
                    self._cached_capabilities = ["basic"]
            
            health = HealthStatus(
                status="healthy",
                message="Server is responding normally",
                timestamp=datetime.now()
            )
            
            self._last_health_check = datetime.now()
            
            return ServerStatus(
                alias=self.server.alias,
                health=health,
                last_successful_connection=datetime.now(),
                response_time_ms=response_time_ms,
                glances_version=self._cached_version,
                capabilities=self._cached_capabilities
            )
        
        except GlancesApiError as e:
            health = HealthStatus(
                status="critical",
                message=f"Health check failed: {e.message}",
                timestamp=datetime.now(),
                details={"status_code": e.status_code}
            )
            
            return ServerStatus(
                alias=self.server.alias,
                health=health,
                last_successful_connection=self._last_health_check,
                glances_version=self._cached_version,
                capabilities=self._cached_capabilities
            )
    
    async def _discover_capabilities(self) -> None:
        """Discover available capabilities by testing endpoints."""
        capabilities = ["basic"]  # Always has basic system info
        
        test_endpoints = [
            ("containers", "docker"),
            ("processes", "processes"),
            ("network", "network"),
            ("diskio", "disk_io"),
            ("fs", "filesystem"),
            ("sensors", "sensors")
        ]
        
        for endpoint, capability in test_endpoints:
            try:
                await self._make_request(endpoint)
                capabilities.append(capability)
            except:
                continue  # Endpoint not available
        
        self._cached_capabilities = capabilities
    
    # Core monitoring methods
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return await self._make_request("system")
    
    async def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information and statistics."""
        return await self._make_request("cpu")
    
    async def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information and statistics."""
        return await self._make_request("mem")
    
    async def get_load_average(self) -> Dict[str, Any]:
        """Get system load averages."""
        return await self._make_request("load")
    
    async def get_uptime(self) -> Dict[str, Any]:
        """Get system uptime."""
        return await self._make_request("uptime")
    
    async def get_disk_usage(self) -> List[Dict[str, Any]]:
        """Get disk usage information."""
        result = await self._make_request("fs")
        return result if isinstance(result, list) else []
    
    async def get_disk_io(self) -> List[Dict[str, Any]]:
        """Get disk I/O statistics."""
        result = await self._make_request("diskio")
        return result if isinstance(result, list) else []
    
    async def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interface statistics."""
        result = await self._make_request("network")
        return result if isinstance(result, list) else []
    
    async def get_network_connections(self) -> List[Dict[str, Any]]:
        """Get network connections."""
        try:
            result = await self._make_request("connections")
            return result if isinstance(result, list) else []
        except GlancesApiError:
            # Connections endpoint might not be available
            return []
    
    async def get_processes(self) -> List[Dict[str, Any]]:
        """Get process list."""
        result = await self._make_request("processlist")
        return result if isinstance(result, list) else []
    
    async def get_containers(self) -> List[Dict[str, Any]]:
        """Get Docker container information."""
        try:
            result = await self._make_request("containers")
            return result if isinstance(result, list) else []
        except GlancesApiError:
            # Containers endpoint might not be available
            return []
    
    async def get_sensors(self) -> Dict[str, Any]:
        """Get sensor information (temperature, etc.)."""
        try:
            return await self._make_request("sensors")
        except GlancesApiError:
            return {}
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Get all available statistics."""
        return await self._make_request("all")


class GlancesClientPool:
    """Pool of Glances clients for managing multiple servers."""
    
    def __init__(self, servers: List[GlancesServer]):
        self.servers = {server.alias: server for server in servers}
        self.clients: Dict[str, GlancesClient] = {}
        self._health_cache: Dict[str, ServerStatus] = {}
        self._health_cache_ttl = 60  # seconds
    
    async def initialize(self) -> None:
        """Initialize all clients."""
        for server in self.servers.values():
            client = GlancesClient(server)
            await client.connect()
            self.clients[server.alias] = client
    
    async def close_all(self) -> None:
        """Close all client connections."""
        tasks = []
        for client in self.clients.values():
            tasks.append(client.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.clients.clear()
    
    def get_client(self, server_alias: str) -> Optional[GlancesClient]:
        """Get client for specific server."""
        return self.clients.get(server_alias)
    
    def get_enabled_clients(self) -> Dict[str, GlancesClient]:
        """Get all clients for enabled servers."""
        enabled_clients = {}
        for alias, server in self.servers.items():
            if server.enabled and alias in self.clients:
                enabled_clients[alias] = self.clients[alias]
        return enabled_clients
    
    async def health_check_all(self, use_cache: bool = True) -> Dict[str, ServerStatus]:
        """Perform health check on all servers."""
        current_time = datetime.now()
        results = {}
        
        # Check cache first if enabled
        if use_cache:
            for alias in self.clients:
                cached_status = self._health_cache.get(alias)
                if cached_status:
                    age = (current_time - cached_status.health.timestamp).total_seconds()
                    if age < self._health_cache_ttl:
                        results[alias] = cached_status
        
        # Health check servers not in cache or cache disabled
        tasks = []
        for alias, client in self.clients.items():
            if alias not in results:
                tasks.append(self._health_check_single(alias, client))
        
        if tasks:
            health_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(health_results):
                alias = list(self.clients.keys())[i]
                if isinstance(result, ServerStatus):
                    results[alias] = result
                    self._health_cache[alias] = result
                elif isinstance(result, Exception):
                    logger.error(
                        "Health check failed for server",
                        server_alias=alias,
                        error=str(result)
                    )
                    # Create failure status
                    results[alias] = ServerStatus(
                        alias=alias,
                        health=HealthStatus(
                            status="critical",
                            message=f"Health check failed: {str(result)}",
                            timestamp=current_time
                        )
                    )
        
        return results
    
    async def _health_check_single(self, alias: str, client: GlancesClient) -> ServerStatus:
        """Perform health check on a single server."""
        try:
            return await async_timeout(client.health_check(), timeout_seconds=10.0)
        except Exception as e:
            return ServerStatus(
                alias=alias,
                health=HealthStatus(
                    status="critical",
                    message=f"Health check timeout: {str(e)}",
                    timestamp=datetime.now()
                )
            )