"""Main MCP server implementation for Glances monitoring."""

import asyncio
from typing import Dict, Any

from fastmcp import FastMCP

from config.models import MCPServerConfig
from config.settings import settings
from glances_mcp.services.alert_engine import AlertEngine
from glances_mcp.services.baseline_manager import BaselineManager
from glances_mcp.services.glances_client import GlancesClientPool
from glances_mcp.services.health_calculator import HealthCalculator
from glances_mcp.tools.advanced_analytics import register_advanced_analytics_tools
from glances_mcp.tools.alert_management import register_alert_management_tools
from glances_mcp.tools.basic_monitoring import register_basic_monitoring_tools
from glances_mcp.tools.capacity_planning import register_capacity_planning_tools
from glances_mcp.prompts.analysis import register_analysis_prompts
from glances_mcp.prompts.troubleshooting import register_troubleshooting_prompts
from glances_mcp.prompts.reporting import register_reporting_prompts
from glances_mcp.resources.configuration import register_configuration_resources
from glances_mcp.utils.logging import logger


class GlancesMCPServer:
    """Main Glances MCP server class."""
    
    def __init__(self):
        self.app = FastMCP(
            name=settings.mcp_server_name,
            version=settings.mcp_server_version
        )
        
        # Core services
        self.config: MCPServerConfig = None
        self.client_pool: GlancesClientPool = None
        self.alert_engine: AlertEngine = None
        self.baseline_manager: BaselineManager = None
        self.health_calculator = HealthCalculator()
        
        # Background tasks
        self._background_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Initialize the MCP server and all services."""
        try:
            logger.info("Initializing Glances MCP Server")
            
            # Load configuration
            self.config = settings.load_mcp_config()
            logger.info(
                "Configuration loaded",
                servers_count=len(self.config.servers),
                enabled_servers=len(self.config.get_enabled_servers())
            )
            
            # Initialize client pool
            self.client_pool = GlancesClientPool(self.config.servers)
            await self.client_pool.initialize()
            logger.info("Glances client pool initialized")
            
            # Initialize baseline manager
            self.baseline_manager = BaselineManager(self.client_pool)
            logger.info("Baseline manager initialized")
            
            # Initialize alert engine
            self.alert_engine = AlertEngine(self.client_pool, self.config)
            logger.info("Alert engine initialized")
            
            # Register all tools, prompts, and resources
            self._register_mcp_components()
            
            logger.info("Glances MCP Server initialized successfully")
        
        except Exception as e:
            logger.error("Failed to initialize Glances MCP Server", error=str(e))
            raise
    
    def _register_mcp_components(self) -> None:
        """Register all MCP tools, prompts, and resources."""
        try:
            # Register tools
            register_basic_monitoring_tools(self.app, self.client_pool)
            register_advanced_analytics_tools(self.app, self.client_pool, self.baseline_manager)
            register_alert_management_tools(self.app, self.client_pool, self.alert_engine)
            register_capacity_planning_tools(self.app, self.client_pool, self.baseline_manager)
            
            logger.info("MCP tools registered")
            
            # Register prompts
            register_analysis_prompts(self.app)
            register_troubleshooting_prompts(self.app)
            register_reporting_prompts(self.app)
            
            logger.info("MCP prompts registered")
            
            # Register resources
            register_configuration_resources(self.app, self.client_pool)
            
            logger.info("MCP resources registered")
        
        except Exception as e:
            logger.error("Failed to register MCP components", error=str(e))
            raise
    
    async def start_background_services(self) -> None:
        """Start background services for continuous monitoring."""
        try:
            # Start baseline collection
            self._background_tasks["baseline_collection"] = asyncio.create_task(
                self.baseline_manager.run_baseline_collection()
            )
            
            # Start alert monitoring
            self._background_tasks["alert_monitoring"] = asyncio.create_task(
                self.alert_engine.run_continuous_monitoring()
            )
            
            logger.info("Background services started")
        
        except Exception as e:
            logger.error("Failed to start background services", error=str(e))
            raise
    
    async def stop_background_services(self) -> None:
        """Stop all background services gracefully."""
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Cancel all background tasks
            for task_name, task in self._background_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(f"Background task {task_name} cancelled")
                    except Exception as e:
                        logger.warning(f"Error stopping background task {task_name}", error=str(e))
            
            self._background_tasks.clear()
            logger.info("Background services stopped")
        
        except Exception as e:
            logger.error("Error stopping background services", error=str(e))
    
    async def shutdown(self) -> None:
        """Shutdown the MCP server and all services."""
        try:
            logger.info("Shutting down Glances MCP Server")
            
            # Stop background services
            await self.stop_background_services()
            
            # Close client pool
            if self.client_pool:
                await self.client_pool.close_all()
                logger.info("Client pool closed")
            
            # Cleanup alert engine
            if self.alert_engine:
                self.alert_engine.cleanup_old_alerts()
                logger.info("Alert engine cleanup completed")
            
            # Cleanup baseline manager
            if self.baseline_manager:
                await self.baseline_manager.cleanup_old_data()
                logger.info("Baseline manager cleanup completed")
            
            logger.info("Glances MCP Server shutdown completed")
        
        except Exception as e:
            logger.error("Error during server shutdown", error=str(e))
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and statistics."""
        try:
            info = {
                "name": settings.mcp_server_name,
                "version": settings.mcp_server_version,
                "status": "running",
                "configuration": {
                    "servers_configured": len(self.config.servers) if self.config else 0,
                    "enabled_servers": len(self.config.get_enabled_servers()) if self.config else 0,
                    "alert_rules": len(self.config.alert_rules) if self.config else 0,
                    "maintenance_windows": len(self.config.maintenance_windows) if self.config else 0
                },
                "services": {
                    "client_pool": "active" if self.client_pool else "inactive",
                    "alert_engine": "active" if self.alert_engine else "inactive", 
                    "baseline_manager": "active" if self.baseline_manager else "inactive"
                },
                "background_tasks": {
                    task_name: "running" if not task.done() else "stopped"
                    for task_name, task in self._background_tasks.items()
                },
                "settings": {
                    "log_level": settings.log_level,
                    "debug": settings.debug,
                    "glances_timeout": settings.glances_timeout,
                    "baseline_retention_days": settings.baseline_retention_days,
                    "alert_history_retention_days": settings.alert_history_retention_days
                }
            }
            
            return info
        
        except Exception as e:
            logger.error("Error getting server info", error=str(e))
            return {
                "name": settings.mcp_server_name,
                "version": settings.mcp_server_version,
                "status": "error",
                "error": str(e)
            }
    
    def get_app(self) -> FastMCP:
        """Get the FastMCP application instance."""
        return self.app


# Global server instance
_server: GlancesMCPServer = None


async def create_server() -> GlancesMCPServer:
    """Create and initialize the Glances MCP server."""
    global _server
    
    if _server is None:
        _server = GlancesMCPServer()
        await _server.initialize()
    
    return _server


async def get_server() -> GlancesMCPServer:
    """Get the current server instance."""
    global _server
    
    if _server is None:
        _server = await create_server()
    
    return _server


async def shutdown_server() -> None:
    """Shutdown the current server instance."""
    global _server
    
    if _server is not None:
        await _server.shutdown()
        _server = None