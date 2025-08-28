"""Modular Starfish MCP tools."""

from typing import Any, Dict, List
import structlog

from mcp.types import Tool, CallToolResult, TextContent

from ..client import StarfishClient
from ..models import StarfishError
from .schema import get_starfish_query_schema
from .starfish_query import execute_starfish_query
from .management import list_volumes, list_zones, get_tagset

logger = structlog.get_logger(__name__)


class StarfishTools:
    """MCP tools for Starfish API operations."""
    
    def __init__(self, client: StarfishClient):
        self.client = client
    
    def get_tools(self) -> List[Tool]:
        """Get list of available MCP tools."""
        return [
            Tool(
                name="starfish_query",
                description="Comprehensive file and directory search in Starfish with all available filters. This is the main search tool.",
                inputSchema=get_starfish_query_schema()
            ),
            
            Tool(
                name="starfish_list_volumes", 
                description="List all available Starfish volumes with details.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            
            Tool(
                name="starfish_list_zones",
                description="List all available Starfish zones with detailed information.",
                inputSchema={
                    "type": "object", 
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            
            Tool(
                name="starfish_get_tagset",
                description="Get detailed information about a specific tagset.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tagset_name": {
                            "type": "string",
                            "description": "Name of the tagset to retrieve (use ':' for default tagset)"
                        }
                    },
                    "required": ["tagset_name"]
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle MCP tool calls."""
        try:
            if name == "starfish_query":
                return await execute_starfish_query(self.client, arguments)
            elif name == "starfish_list_volumes":
                return await list_volumes(self.client, arguments)
            elif name == "starfish_list_zones":
                return await list_zones(self.client, arguments)
            elif name == "starfish_get_tagset":
                return await get_tagset(self.client, arguments)
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )],
                    isError=True
                )
        except StarfishError as e:
            logger.error("Starfish API error", tool=name, error=str(e))
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Starfish API error: {e}"
                )],
                isError=True
            )
        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e))
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Tool execution failed: {e}"
                )],
                isError=True
            )


# For backward compatibility, export the class
__all__ = ["StarfishTools"]
