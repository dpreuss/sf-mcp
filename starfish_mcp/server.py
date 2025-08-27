"""Main MCP server for Starfish integration."""

import asyncio
import sys
from typing import Any, Sequence
import structlog

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ToolResult,
    EmbeddedResource,
)

from .config import load_config, StarfishConfig
from .client import StarfishClient
from .tools import StarfishTools


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class StarfishMCPServer:
    """MCP Server for Starfish Storage integration."""
    
    def __init__(self, config: StarfishConfig):
        self.config = config
        self.server = Server("starfish-mcp")
        self.client: StarfishClient = None
        self.tools: StarfishTools = None
        
        # Configure logging level
        logging_level = getattr(structlog.stdlib, config.log_level, structlog.INFO)
        structlog.configure(
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup MCP server handlers
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup MCP server message handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            if self.tools is None:
                return []
            return self.tools.get_tools()
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> ToolResult:
            """Handle tool calls."""
            if self.tools is None:
                return ToolResult(
                    content=[TextContent(
                        type="text",
                        text="Starfish client not initialized"
                    )],
                    isError=True
                )
            
            return await self.tools.handle_tool_call(name, arguments or {})
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available resources."""
            # For now, we don't expose any static resources
            # Could be extended to expose configuration, API status, etc.
            return []
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource content."""
            # Not implemented yet
            raise NotImplementedError("Resource reading not implemented")
    
    async def initialize(self) -> None:
        """Initialize the Starfish client."""
        logger.info(
            "Initializing Starfish MCP server",
            api_endpoint=self.config.api_endpoint,
            file_server_url=self.config.file_server_url
        )
        
        try:
            # Initialize Starfish client
            self.client = StarfishClient(self.config)
            
            # Test connection by listing collections
            async with self.client:
                collections = await self.client.list_collections()
                logger.info(
                    "Successfully connected to Starfish API",
                    total_collections=len(collections)
                )
            
            # Initialize tools
            self.tools = StarfishTools(self.client)
            
            logger.info("Starfish MCP server initialized successfully")
            
        except Exception as e:
            logger.error(
                "Failed to initialize Starfish MCP server",
                error=str(e)
            )
            raise
    
    async def run(self) -> None:
        """Run the MCP server."""
        try:
            await self.initialize()
            
            # Setup server options
            options = InitializationOptions(
                server_name="starfish-mcp",
                server_version="0.1.0",
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
            
            logger.info("Starting MCP server")
            
            # Run the server
            async with self.server.run_as_async_context_manager(
                stdin=sys.stdin.buffer,
                stdout=sys.stdout.buffer
            ) as streams:
                await streams.run()
                
        except Exception as e:
            logger.error(
                "MCP server error",
                error=str(e)
            )
            raise
        finally:
            # Clean up client connection
            if self.client:
                await self.client.close()
                logger.info("Starfish client closed")


async def main() -> None:
    """Main entry point."""
    try:
        # Load configuration
        config = load_config()
        
        # Create and run server
        server = StarfishMCPServer(config)
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(
            "Server startup failed",
            error=str(e)
        )
        sys.exit(1)


def main_sync() -> None:
    """Synchronous main entry point for console scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
