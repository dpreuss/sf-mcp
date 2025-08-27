"""MCP tools for Starfish operations."""

import json
from typing import Any, Dict, List, Optional
import structlog

from mcp.server.models import Tool
from mcp.types import (
    TextContent,
    ToolResult,
    EmbeddedResource,
)

from .client import StarfishClient
from .models import StarfishError


logger = structlog.get_logger(__name__)


class StarfishTools:
    """MCP tools for Starfish API operations."""
    
    def __init__(self, client: StarfishClient):
        self.client = client
    
    def get_tools(self) -> List[Tool]:
        """Get list of available MCP tools."""
        return [
            Tool(
                name="starfish_find_file",
                description="Find files by name in Starfish. Simple search for files matching a filename pattern.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Filename or pattern to search for (e.g., 'foo', '*.pdf', 'config.json')"
                        },
                        "collection": {
                            "type": "string", 
                            "description": "Optional collection name to search within (e.g., 'Documents', 'TestData')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 100)",
                            "default": 100
                        }
                    },
                    "required": ["filename"]
                }
            ),
            Tool(
                name="starfish_find_by_tag",
                description="Find files with specific tags in Starfish.",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "tag": {
                            "type": "string",
                            "description": "Tag to search for (e.g., 'bar', 'project:alpha', 'status:active')"
                        },
                        "collection": {
                            "type": "string",
                            "description": "Optional collection name to search within"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 100)", 
                            "default": 100
                        }
                    },
                    "required": ["tag"]
                }
            ),
            Tool(
                name="starfish_find_in_directory",
                description="Find files in a specific directory path in Starfish.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory path to search in (e.g., '/baz', '/data/projects')"
                        },
                        "collection": {
                            "type": "string",
                            "description": "Optional collection name to search within"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to search recursively in subdirectories (default: true)",
                            "default": True
                        },
                        "limit": {
                            "type": "integer", 
                            "description": "Maximum number of results to return (default: 100)",
                            "default": 100
                        }
                    },
                    "required": ["directory_path"]
                }
            ),
            Tool(
                name="starfish_query_advanced",
                description="Execute advanced Starfish query with full control over query parameters.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Starfish query string (e.g., 'type=f size>1MB tag=important')"
                        },
                        "format_fields": {
                            "type": "string",
                            "description": "Space-separated list of fields to return (e.g., 'fn size mt volume tags_explicit')",
                            "default": "parent_path fn type size ct mt at uid gid mode volume tags_explicit tags_inherited"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 1000)",
                            "default": 1000
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort order (e.g., 'size', 'mt', 'parent_path,fn')"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="starfish_list_volumes",
                description="List all available Starfish volumes and their mount information.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            Tool(
                name="starfish_list_collections", 
                description="List all available Starfish collections (Collections: tagset).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "force_refresh": {
                            "type": "boolean",
                            "description": "Force refresh of collections cache (default: false)",
                            "default": False
                        }
                    },
                    "additionalProperties": False
                }
            ),
            Tool(
                name="starfish_get_tagset",
                description="Get all tags from a specific tagset.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tagset_name": {
                            "type": "string",
                            "description": "Name of the tagset to query (e.g., 'Collections', 'Projects')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tags to return (default: 1000)",
                            "default": 1000
                        },
                        "with_private": {
                            "type": "boolean",
                            "description": "Include private tags in results (default: true)",
                            "default": True
                        }
                    },
                    "required": ["tagset_name"]
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
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Handle MCP tool calls."""
        try:
            if name == "starfish_find_file":
                return await self._find_file(arguments)
            elif name == "starfish_find_by_tag":
                return await self._find_by_tag(arguments)
            elif name == "starfish_find_in_directory":
                return await self._find_in_directory(arguments)
            elif name == "starfish_query_advanced":
                return await self._query_advanced(arguments)
            elif name == "starfish_list_volumes":
                return await self._list_volumes(arguments)
            elif name == "starfish_list_collections":
                return await self._list_collections(arguments)
            elif name == "starfish_get_tagset":
                return await self._get_tagset(arguments)
            elif name == "starfish_list_zones":
                return await self._list_zones(arguments)
            else:
                return ToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )],
                    isError=True
                )
        
        except StarfishError as e:
            logger.error(
                "Starfish API error",
                tool=name,
                error_code=e.code,
                error_message=e.message
            )
            return ToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Starfish API Error ({e.code}): {e.message}"
                )],
                isError=True
            )
        
        except Exception as e:
            logger.error(
                "Tool execution error", 
                tool=name,
                error=str(e)
            )
            return ToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Tool execution failed: {str(e)}"
                )],
                isError=True
            )
    
    async def _find_file(self, arguments: Dict[str, Any]) -> ToolResult:
        """Find files by filename."""
        filename = arguments["filename"]
        collection = arguments.get("collection")
        limit = arguments.get("limit", 100)
        
        # Build query
        query_parts = ["type=f"]  # Only files
        
        # Add filename filter - use wildcard matching
        if "*" in filename or "?" in filename:
            # TODO: Starfish may not support glob patterns directly in filename search
            # For now, we'll do a simple contains search and filter results
            query_parts.append(f"fn~{filename.replace('*', '').replace('?', '')}")
        else:
            query_parts.append(f"fn~{filename}")
        
        # Add collection filter if specified
        if collection:
            query_parts.append(f"tag=Collections:{collection}")
        
        query = " ".join(query_parts)
        
        logger.info(
            "Searching for files by name",
            filename=filename,
            collection=collection,
            query=query
        )
        
        response = await self.client.query(query, limit=limit)
        
        # Filter results for exact filename matches if needed
        filtered_entries = []
        for entry in response.entries:
            if "*" in filename:
                # Simple wildcard matching
                pattern = filename.replace("*", ".*").replace("?", ".")
                import re
                if re.match(pattern, entry.filename, re.IGNORECASE):
                    filtered_entries.append(entry)
            elif filename.lower() in entry.filename.lower():
                filtered_entries.append(entry)
        
        # Convert to JSON
        results = []
        for entry in filtered_entries[:limit]:
            results.append({
                "id": entry.id,
                "filename": entry.filename,
                "parent_path": entry.parent_path,
                "full_path": entry.full_path,
                "size": entry.size,
                "volume": entry.volume,
                "modify_time": entry.modify_time.isoformat() if entry.modify_time else None,
                "tags_explicit": entry.tags_explicit,
                "tags_inherited": entry.tags_inherited,
                "is_file": entry.is_file
            })
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "total_found": len(filtered_entries),
                    "returned": len(results),
                    "files": results
                }, indent=2)
            )]
        )
    
    async def _find_by_tag(self, arguments: Dict[str, Any]) -> ToolResult:
        """Find files by tag."""
        tag = arguments["tag"]
        collection = arguments.get("collection")
        limit = arguments.get("limit", 100)
        
        # Build query
        query_parts = ["type=f"]  # Only files
        query_parts.append(f"tag={tag}")
        
        # Add collection filter if specified
        if collection:
            query_parts.append(f"tag=Collections:{collection}")
        
        query = " ".join(query_parts)
        
        logger.info(
            "Searching for files by tag",
            tag=tag,
            collection=collection,
            query=query
        )
        
        response = await self.client.query(query, limit=limit)
        
        # Convert to JSON
        results = []
        for entry in response.entries:
            results.append({
                "id": entry.id,
                "filename": entry.filename,
                "parent_path": entry.parent_path,
                "full_path": entry.full_path,
                "size": entry.size,
                "volume": entry.volume,
                "modify_time": entry.modify_time.isoformat() if entry.modify_time else None,
                "tags_explicit": entry.tags_explicit,
                "tags_inherited": entry.tags_inherited,
                "is_file": entry.is_file
            })
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "total_found": response.total,
                    "returned": len(results),
                    "files": results
                }, indent=2)
            )]
        )
    
    async def _find_in_directory(self, arguments: Dict[str, Any]) -> ToolResult:
        """Find files in directory."""
        directory_path = arguments["directory_path"].rstrip("/")
        collection = arguments.get("collection")
        recursive = arguments.get("recursive", True)
        limit = arguments.get("limit", 100)
        
        # Build query
        query_parts = ["type=f"]  # Only files
        
        if recursive:
            # Search in directory and all subdirectories
            query_parts.append(f"parent_path~{directory_path}")
        else:
            # Search only in exact directory
            query_parts.append(f"parent_path={directory_path}")
        
        # Add collection filter if specified
        if collection:
            query_parts.append(f"tag=Collections:{collection}")
        
        query = " ".join(query_parts)
        
        logger.info(
            "Searching for files in directory",
            directory_path=directory_path,
            collection=collection,
            recursive=recursive,
            query=query
        )
        
        response = await self.client.query(query, limit=limit)
        
        # Convert to JSON
        results = []
        for entry in response.entries:
            results.append({
                "id": entry.id,
                "filename": entry.filename,
                "parent_path": entry.parent_path,
                "full_path": entry.full_path,
                "size": entry.size,
                "volume": entry.volume,
                "modify_time": entry.modify_time.isoformat() if entry.modify_time else None,
                "tags_explicit": entry.tags_explicit,
                "tags_inherited": entry.tags_inherited,
                "is_file": entry.is_file
            })
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "directory_path": directory_path,
                    "recursive": recursive,
                    "total_found": response.total,
                    "returned": len(results),
                    "files": results
                }, indent=2)
            )]
        )
    
    async def _query_advanced(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute advanced query."""
        query = arguments["query"]
        format_fields = arguments.get("format_fields")
        limit = arguments.get("limit", 1000)
        sort_by = arguments.get("sort_by")
        
        logger.info(
            "Executing advanced query",
            query=query,
            format_fields=format_fields,
            limit=limit,
            sort_by=sort_by
        )
        
        response = await self.client.query(
            query=query,
            format_fields=format_fields,
            limit=limit,
            sort_by=sort_by
        )
        
        # Convert to JSON
        results = []
        for entry in response.entries:
            results.append({
                "id": entry.id,
                "filename": entry.filename,
                "parent_path": entry.parent_path,
                "full_path": entry.full_path,
                "type": entry.type,
                "size": entry.size,
                "volume": entry.volume,
                "create_time": entry.create_time.isoformat() if entry.create_time else None,
                "modify_time": entry.modify_time.isoformat() if entry.modify_time else None,
                "access_time": entry.access_time.isoformat() if entry.access_time else None,
                "uid": entry.uid,
                "gid": entry.gid,
                "mode": entry.mode,
                "tags_explicit": entry.tags_explicit,
                "tags_inherited": entry.tags_inherited,
                "is_file": entry.is_file
            })
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "total_found": response.total,
                    "returned": len(results),
                    "entries": results
                }, indent=2)
            )]
        )
    
    async def _list_volumes(self, arguments: Dict[str, Any]) -> ToolResult:
        """List volumes."""
        logger.info("Listing volumes")
        
        volumes = await self.client.list_volumes()
        
        # Convert to JSON
        results = []
        for volume in volumes:
            results.append({
                "id": volume.id,
                "volume_name": volume.vol,
                "display_name": volume.display_name,
                "type": volume.type,
                "mounts": volume.mounts,
                "mount_opts": volume.mount_opts
            })
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "total_volumes": len(results),
                    "volumes": results
                }, indent=2)
            )]
        )
    
    async def _list_collections(self, arguments: Dict[str, Any]) -> ToolResult:
        """List collections."""
        force_refresh = arguments.get("force_refresh", False)
        
        logger.info("Listing collections", force_refresh=force_refresh)
        
        collections = await self.client.list_collections(force_refresh=force_refresh)
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "total_collections": len(collections),
                    "collections": collections
                }, indent=2)
            )]
        )
    
    async def _get_tagset(self, arguments: Dict[str, Any]) -> ToolResult:
        """Get tagset."""
        tagset_name = arguments["tagset_name"]
        limit = arguments.get("limit", 1000)
        with_private = arguments.get("with_private", True)
        
        logger.info(
            "Getting tagset",
            tagset_name=tagset_name,
            limit=limit,
            with_private=with_private
        )
        
        tagset_response = await self.client.get_tagset(
            tagset_name=tagset_name,
            limit=limit,
            with_private=with_private
        )
        
        # Extract tag names
        tag_names = [tag.name for tag in tagset_response.tag_names]
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "tagset_name": tagset_name,
                    "total_tags": len(tag_names),
                    "tags": tag_names
                }, indent=2)
            )]
        )
    
    async def _list_zones(self, arguments: Dict[str, Any]) -> ToolResult:
        """List zones."""
        logger.info("Listing zones")
        
        zones = await self.client.list_zones()
        
        # Convert to JSON
        results = []
        for zone in zones:
            zone_data = {
                "id": zone.id,
                "name": zone.name,
                "managers": [
                    {
                        "system_id": manager.system_id,
                        "username": manager.username
                    }
                    for manager in zone.managers
                ],
                "managing_groups": [
                    {
                        "system_id": group.system_id,
                        "groupname": group.groupname
                    }
                    for group in zone.managing_groups
                ],
                "restore_managers": zone.restore_managers,
                "restore_managing_groups": zone.restore_managing_groups,
                "paths": zone.paths,
                "tagsets": [
                    {
                        "name": tagset.name,
                        "tag_names": tagset.tag_names
                    }
                    for tagset in zone.tagsets
                ],
                "user_params": zone.user_params,
                "aggregates": {
                    "size": zone.aggregates.size if zone.aggregates else None,
                    "dirs": zone.aggregates.dirs if zone.aggregates else None,
                    "files": zone.aggregates.files if zone.aggregates else None,
                    "cost": zone.aggregates.cost if zone.aggregates else None
                } if zone.aggregates else None
            }
            results.append(zone_data)
        
        return ToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "total_zones": len(results),
                    "zones": results
                }, indent=2)
            )]
        )
