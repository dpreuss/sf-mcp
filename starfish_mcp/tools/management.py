"""Starfish management tools - volumes, zones, tagsets."""

import json
from typing import Any, Dict
import structlog

from mcp.types import TextContent

from ..client import StarfishClient
from ..models import StarfishError

logger = structlog.get_logger(__name__)


async def list_volumes(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
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
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "total_volumes": len(results),
                    "volumes": results
                }, indent=2)
            }
        ]
    }


async def list_zones(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
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
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "total_zones": len(results),
                    "zones": results
                }, indent=2)
            }
        ]
    }


async def get_tagset(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
    """Get detailed information about a specific tagset."""
    tagset_name = arguments["tagset_name"]
    
    logger.info("Getting tagset details", tagset_name=tagset_name)
    
    tagset_data = await client.get_tagset(tagset_name)
    
    # Parse the raw dict response into a model
    from ..models import StarfishTagsetResponse
    tagset = StarfishTagsetResponse(**tagset_data)
    
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
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }


async def list_tagsets(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
    """List all available tagsets with their details."""
    logger.info("Listing Starfish tagsets")
    
    tagsets_data = await client.list_tagsets()
    
    # Convert to more readable format
    results = []
    for tagset in tagsets_data:
        tagset_info = {
            "name": tagset.get("name"),
            "zone_ids": tagset.get("zone_ids", []),
            "inheritable": tagset.get("inheritable", False),
            "pinnable": tagset.get("pinnable", False),
            "action": tagset.get("action"),
            "tag_count": len(tagset.get("tags", [])),
            "zone_count": len(tagset.get("zones", []))
        }
        
        # Add sample tags if available
        tags = tagset.get("tags", [])
        if tags:
            tagset_info["sample_tags"] = [tag.get("name") for tag in tags[:5]]  # First 5 tags
            if len(tags) > 5:
                tagset_info["sample_tags"].append(f"... and {len(tags) - 5} more")
        
        results.append(tagset_info)
    
    # Sort by name
    results.sort(key=lambda x: x.get("name", ""))
    
    result = {
        "total_tagsets": len(results),
        "tagsets": results,
        "note": "Use starfish_get_tagset with any tagset name to get complete details including all tags"
    }
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }


async def get_zone(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
    """Get detailed information about a specific zone by ID."""
    zone_id = arguments["zone_id"]
    
    logger.info("Getting zone details", zone_id=zone_id)
    
    zone_data = await client.get_zone(zone_id)
    
    # Format the zone data
    result = {
        "id": zone_data.get("id"),
        "name": zone_data.get("name"),
        "paths": zone_data.get("paths", []),
        "managers": zone_data.get("managers", []),
        "managing_groups": zone_data.get("managing_groups", []),
        "restore_managers": zone_data.get("restore_managers", []),
        "restore_managing_groups": zone_data.get("restore_managing_groups", []),
        "tagsets": zone_data.get("tagsets", []),
        "user_params": zone_data.get("user_params", {}),
        "aggregates": zone_data.get("aggregates")
    }
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }


async def get_volume(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
    """Get detailed information about a specific volume by ID."""
    volume_id = arguments["volume_id"]
    
    logger.info("Getting volume details", volume_id=volume_id)
    
    volume_data = await client.get_volume(volume_id)
    
    # Format the volume data
    result = {
        "id": volume_data.get("id"),
        "name": volume_data.get("vol"),
        "display_name": volume_data.get("display_name"),
        "root": volume_data.get("root"),
        "type": volume_data.get("type"),
        "default_agent_address": volume_data.get("default_agent_address"),
        "total_capacity": volume_data.get("total_capacity"),
        "free_space": volume_data.get("free_space"),
        "mounts": volume_data.get("mounts", []),
        "mount_opts": volume_data.get("mount_opts", {}),
        "volume_size_info": volume_data.get("volume_size_info")
    }
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }


async def list_tags(client: StarfishClient, arguments: Dict[str, Any]) -> dict:
    """List all available tags/tagsets."""
    logger.info("Listing Starfish tags")
    
    force_refresh = arguments.get("force_refresh", False)
    
    collections = await client.list_collections(force_refresh=force_refresh)
    
    result = {
        "total_tagsets": len(collections),
        "tagsets": collections,
        "note": "Use starfish_get_tagset with any of these names to get detailed tagset information"
    }
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }
