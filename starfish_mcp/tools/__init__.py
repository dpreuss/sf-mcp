"""Modular Starfish MCP tools."""

from typing import Any, Dict, List
import structlog

from mcp.types import Tool, TextContent

from ..client import StarfishClient
from ..models import StarfishError
from .schema import get_starfish_query_schema
from .starfish_query import execute_starfish_query
from .management import list_volumes, list_zones, get_tagset, list_tags, list_tagsets, get_zone, get_volume

logger = structlog.get_logger(__name__)


class StarfishTools:
    """MCP tools for Starfish API operations."""
    
    def __init__(self, client: StarfishClient):
        self.client = client
        self._query_count = 0  # Track queries to enforce guardrails
        
    def reset_query_count(self):
        """Reset query count for new session/conversation."""
        self._query_count = 0
    
    def get_tools(self) -> List[Tool]:
        """Get list of available MCP tools."""
        return [
            Tool(
                name="starfish_query", 
                description="""Comprehensive file and directory search in Starfish with all available filters. Returns detailed metadata including timestamps, permissions, ownership, zones, and tags. Use 'format_fields' parameter to control output detail level. This is the main search tool.

🚨 CRITICAL GUARDRAILS:
- NEVER run more than 5 sequential queries to solve one problem - if you need more, you're solving it wrong
- Each query has a 20-second timeout - plan accordingly  
- Use broad queries instead of iterating through volumes/directories individually

OPTIMIZATION TIPS:
- Use 'total_found' from response for counts - set limit=0 when you only need counts, don't count results manually
- For directory analysis: use file_type='d', depth=1, format_fields='fn rec_aggrs', sort_by='-rec_aggrs.size'
- Use 'fn' for filename (not 'name'), 'rec_aggrs' becomes 'recursive_aggregates' in output
- recursive_aggregates.size = logical directory tree size, recursive_aggregates.files = file count
- For tag analysis: set tag='tag_name', limit=0, read total_found for count
- For largest files: file_type='f', sort_by='-size', format_fields='parent_path fn size'

ANTI-PATTERNS TO AVOID:
❌ for volume in volumes: query(volumes_and_paths=[volume]) # Multiple queries!
✅ query(volumes_and_paths=[], format_fields="fn rec_aggrs") # Single broad query""",
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
                name="starfish_get_zone", 
                description="Get detailed information about a specific Starfish zone by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zone_id": {
                            "type": "integer",
                            "description": "ID of the zone to retrieve"
                        }
                    },
                    "required": ["zone_id"]
                }
            ),
            Tool(
                name="starfish_get_volume", 
                description="Get detailed information about a specific Starfish volume by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "volume_id": {
                            "type": "integer",
                            "description": "ID of the volume to retrieve"
                        }
                    },
                    "required": ["volume_id"]
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
            ),
            Tool(
                name="starfish_list_tagsets",
                description="List all available tagsets with detailed information including tag counts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "random_string": {
                            "type": "string",
                            "description": "Dummy parameter for no-parameter tools"
                        }
                    },
                    "required": ["random_string"]
                }
            ),
            Tool(
                name="starfish_list_tags",
                description="List all available tags/tagsets in Starfish.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "force_refresh": {
                            "type": "boolean",
                            "description": "Force refresh of tags list from server",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="starfish_reset_query_count",
                description="Reset the query count guardrail. Use this when starting a new task if you've hit the 5-query limit.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]):
        """Handle MCP tool calls."""
        try:
            if name == "starfish_query":
                # Enforce query limit guardrail
                self._query_count += 1
                if self._query_count > 5:
                    logger.warning(
                        "Query limit exceeded", 
                        query_count=self._query_count,
                        limit=5
                    )
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"🚨 GUARDRAIL VIOLATION: Query limit exceeded ({self._query_count}/5 queries). "
                                       f"You're probably solving this problem incorrectly. "
                                       f"Use broader queries instead of multiple narrow ones. "
                                       f"Call reset_query_count() if you're starting a new task."
                            }
                        ]
                    }
                    
                return await execute_starfish_query(self.client, arguments)
            elif name == "starfish_list_volumes":
                return await list_volumes(self.client, arguments)
            elif name == "starfish_list_zones":
                return await list_zones(self.client, arguments)
            elif name == "starfish_get_zone":
                return await get_zone(self.client, arguments)
            elif name == "starfish_get_volume":
                return await get_volume(self.client, arguments)
            elif name == "starfish_get_tagset":
                return await get_tagset(self.client, arguments)
            elif name == "starfish_list_tagsets":
                return await list_tagsets(self.client, arguments)
            elif name == "starfish_list_tags":
                return await list_tags(self.client, arguments)
            elif name == "starfish_reset_query_count":
                self.reset_query_count()
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Query count reset to 0. You can now run up to 5 more queries."
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {name}"
                        }
                    ]
                }
        except StarfishError as e:
            logger.error("Starfish API error", tool=name, error=str(e))
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Starfish API error: {e}"
                    }
                ]
            }
        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e))
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool execution failed: {e}"
                    }
                ]
            }


# For backward compatibility, export the class
__all__ = ["StarfishTools"]
