"""Starfish management tools - volumes, zones, tagsets."""

import json
from typing import Any, Dict
import structlog

from mcp.types import CallToolResult, TextContent

from ..client import StarfishClient
from ..models import StarfishError

logger = structlog.get_logger(__name__)


async def list_volumes(client: StarfishClient, arguments: Dict[str, Any]) -> CallToolResult:
    """List available Starfish volumes."""
    logger.info("Listing Starfish volumes")
    
    volumes = await client.list_volumes()
    
    # Convert to JSON
    results = []
    for volume in volumes:
        volume_data = {
            "id": volume.id,
            "name": volume.vol,
            "display_name": volume.display_name,
            "root": volume.root,
            "type": volume.type,
            "default_agent_address": volume.default_agent_address,
            "total_capacity": volume.total_capacity,
            "free_space": volume.free_space,
            "mounts": volume.mounts,
            "mount_opts": volume.mount_opts
        }
        
        # Add volume size info if available
        if volume.volume_size_info:
            volume_data["size_info"] = {
                "number_of_files": volume.number_of_files,
                "number_of_dirs": volume.number_of_dirs,
                "sum_of_logical_sizes": volume.sum_of_logical_sizes,
                "sum_of_physical_sizes": volume.sum_of_physical_sizes,
                "sum_of_blocks": volume.sum_of_blocks
            }
        
        results.append(volume_data)
    
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=json.dumps({
                "total_volumes": len(results),
                "volumes": results
            }, indent=2)
        )]
    )


async def list_zones(client: StarfishClient, arguments: Dict[str, Any]) -> CallToolResult:
    """List available Starfish zones."""
    logger.info("Listing Starfish zones")
    
    zones = await client.list_zones()
    
    # Convert to JSON
    results = []
    for zone in zones:
        zone_data = {
            "id": zone.id,
            "name": zone.name,
            "paths": zone.paths,
            "managers": [{"system_id": m.system_id, "username": m.username} for m in zone.managers],
            "managing_groups": [{"system_id": g.system_id, "groupname": g.groupname} for g in zone.managing_groups],
            "restore_managers": zone.restore_managers,
            "restore_managing_groups": zone.restore_managing_groups,
            "tagsets": [{"name": t.name, "tag_names": t.tag_names} for t in zone.tagsets],
            "user_params": zone.user_params,
            "aggregates": {
                "size": zone.aggregates.size if zone.aggregates else None,
                "dirs": zone.aggregates.dirs if zone.aggregates else None,
                "files": zone.aggregates.files if zone.aggregates else None,
                "cost": zone.aggregates.cost if zone.aggregates else None
            } if zone.aggregates else None
        }
        results.append(zone_data)
    
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=json.dumps({
                "total_zones": len(results),
                "zones": results
            }, indent=2)
        )]
    )


async def get_tagset(client: StarfishClient, arguments: Dict[str, Any]) -> CallToolResult:
    """Get detailed information about a specific tagset."""
    tagset_name = arguments["tagset_name"]
    
    logger.info("Getting tagset details", tagset_name=tagset_name)
    
    tagset = await client.get_tagset(tagset_name)
    
    # Convert to JSON
    result = {
        "name": tagset.name,
        "zone_ids": tagset.zone_ids,
        "inheritable": tagset.inheritable,
        "pinnable": tagset.pinnable,
        "action": tagset.action.value if tagset.action else None,
        "tags": [{"id": tag.id, "name": tag.name} for tag in tagset.tags],
        "zones": []
    }
    
    # Add zone details
    for zone in tagset.zones:
        zone_data = {
            "id": zone.id,
            "name": zone.name,
            "paths": zone.paths,
            "managers": [{"system_id": m.system_id, "username": m.username} for m in zone.managers],
            "managing_groups": [{"system_id": g.system_id, "groupname": g.groupname} for g in zone.managing_groups],
            "tagsets": [{"name": t.name, "tag_names": t.tag_names} for t in zone.tagsets],
            "user_params": zone.user_params
        }
        result["zones"].append(zone_data)
    
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    )
