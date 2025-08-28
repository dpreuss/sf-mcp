"""Starfish comprehensive query tool implementation."""

import json
from typing import Any, Dict, List
import structlog

from mcp.types import CallToolResult, TextContent

from ..client import StarfishClient
from ..models import StarfishError
from .query_builder import build_starfish_query, extract_query_metadata

logger = structlog.get_logger(__name__)


async def execute_starfish_query(client: StarfishClient, arguments: Dict[str, Any]) -> CallToolResult:
    """Execute comprehensive Starfish query with all available filters."""
    
    # Extract execution parameters
    volumes_and_paths = arguments.get("volumes_and_paths", [])
    limit = arguments.get("limit", 100)
    sort_by = arguments.get("sort_by")
    format_fields = arguments.get("format_fields")
    use_async = arguments.get("use_async", False)
    
    # Build query string
    query = build_starfish_query(arguments)
    
    logger.info(
        "Executing comprehensive Starfish query",
        query=query,
        volumes_and_paths=volumes_and_paths,
        use_async=use_async,
        limit=limit
    )
    
    # Execute query
    if use_async and volumes_and_paths:
        response = await client.async_query(
            volumes_and_paths=volumes_and_paths,
            queries=[query] if query else [],
            format_fields=format_fields,
            limit=limit,
            sort_by=sort_by
        )
    else:
        volumes_param = volumes_and_paths[0] if volumes_and_paths else None
        response = await client.query(
            query=query,
            volumes_and_paths=volumes_param,
            format_fields=format_fields,
            limit=limit,
            sort_by=sort_by
        )
    
    # Convert to JSON result
    results = []
    for entry in response:
        result = {
            "id": entry.id,
            "filename": entry.filename,
            "parent_path": entry.parent_path,
            "full_path": entry.full_path,
            "volume": entry.volume,
            "size": entry.size,
            "type": "file" if entry.is_file else "directory",
            "uid": entry.uid,
            "gid": entry.gid,
            "mode": entry.mode
        }
        
        # Add time information if available
        if entry.create_time:
            result["create_time"] = entry.create_time.isoformat()
        if entry.modify_time:
            result["modify_time"] = entry.modify_time.isoformat()
        if entry.access_time:
            result["access_time"] = entry.access_time.isoformat()
        
        # Add tags if available
        if entry.all_tags:
            result["tags"] = entry.all_tags
        
        # Add zones if available
        if entry.zones:
            result["zones"] = [{"id": z.id, "name": z.name, "relative_path": z.relative_path} for z in entry.zones]
        
        results.append(result)
    
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=json.dumps({
                "query": query,
                "filters_applied": extract_query_metadata(arguments),
                "search_scope": volumes_and_paths,
                "use_async": use_async,
                "total_found": len(results),
                "limit": limit,
                "results": results
            }, indent=2)
        )]
    )
