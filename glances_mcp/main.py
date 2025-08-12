"""Main application entry point for Glances MCP server."""

import argparse
import asyncio
import signal
import sys
from pathlib import Path

from glances_mcp.config.settings import settings
from glances_mcp.server import create_server, shutdown_server
from glances_mcp.utils.logging import logger


async def main() -> None:
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Glances MCP Server - Infrastructure monitoring via Model Context Protocol"
    )
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "--host",
        type=str, 
        help="Host to bind to",
        default=None
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to", 
        default=None
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
        default=None
    )
    
    args = parser.parse_args()
    
    # Override settings with command line arguments
    if args.config:
        settings.config_file = args.config
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
    if args.debug:
        settings.debug = True
    if args.log_level:
        settings.log_level = args.log_level
    
    # Validate configuration file exists if specified
    config_path = Path(settings.config_file)
    if not config_path.exists():
        logger.warning(
            "Configuration file not found, using default configuration",
            config_file=str(config_path)
        )
    
    logger.info(
        "Starting Glances MCP Server",
        version=settings.mcp_server_version,
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        config_file=settings.config_file
    )
    
    # Create and initialize the server
    server = None
    try:
        server = await create_server()
        
        # Start background services
        await server.start_background_services()
        
        # Set up signal handlers for graceful shutdown
        shutdown_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown")
            shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Get the FastMCP app
        app = server.get_app()
        
        logger.info("Glances MCP Server started successfully")
        logger.info(f"Server info: {server.get_server_info()}")
        
        # Run the server
        try:
            # Start FastMCP server
            await app.run(
                transport="stdio",  # Use stdio transport for MCP
                host=settings.host,
                port=settings.port
            )
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            shutdown_event.set()
        
        # Wait for shutdown signal
        await shutdown_event.wait()
    
    except Exception as e:
        logger.error("Fatal error in main application", error=str(e))
        sys.exit(1)
    
    finally:
        # Cleanup
        if server:
            logger.info("Shutting down server")
            await shutdown_server()
        
        logger.info("Glances MCP Server stopped")


def run_server() -> None:
    """Run the server with proper event loop handling."""
    try:
        # Python 3.11+ compatibility
        if sys.version_info >= (3, 11):
            with asyncio.Runner() as runner:
                runner.run(main())
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Fatal error running server", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    run_server()