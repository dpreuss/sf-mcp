"""Starfish query parameter schemas and definitions."""

from typing import Dict, Any


def get_starfish_query_schema() -> Dict[str, Any]:
    """Get the comprehensive starfish_query tool input schema."""
    return {
        "type": "object",
        "properties": {
            # Basic search parameters
            "name": {
                "type": "string",
                "description": "Filename pattern (shell wildcards: *, ?). Examples: 'config.json', '*.pdf', 'test*'"
            },
            "name_regex": {
                "type": "string", 
                "description": "Filename regex pattern. Examples: '^.*\\.jpg$', '^config.*\\.json$'"
            },
            "path": {
                "type": "string",
                "description": "Parent path pattern (shell wildcards). Examples: '/home/*', 'Documents/Projects'"
            },
            "path_regex": {
                "type": "string",
                "description": "Parent path regex pattern. Examples: '^/home/.*', '^.*project.*$'"
            },
            
            # File attributes
            "file_type": {
                "type": "string",
                "enum": ["f", "d", "l", "b", "c", "s", "p"],
                "description": "File type: 'f'=file, 'd'=directory, 'l'=symlink, 'b'=block device, 'c'=char device, 's'=socket, 'p'=FIFO"
            },
            "ext": {
                "type": "string",
                "description": "File extension (without dot). Examples: 'pdf', 'jpg', 'txt'"
            },
            "empty": {
                "type": "boolean",
                "description": "Find empty files and directories (true) or exclude them (false)"
            },
            
            # Ownership and permissions
            "uid": {
                "type": "integer",
                "description": "User ID (UID) to filter by. Examples: 0 (root), 1001"
            },
            "gid": {
                "type": "integer",
                "description": "Group ID (GID) to filter by. Examples: 0 (root group), 100"
            },
            "username": {
                "type": "string",
                "description": "Username (exact match). Examples: 'root', 'john', 'admin'"
            },
            "username_regex": {
                "type": "string",
                "description": "Username regex pattern. Examples: '^admin.*', '^.*_user$'"
            },
            "groupname": {
                "type": "string", 
                "description": "Group name (exact match). Examples: 'wheel', 'users', 'admin'"
            },
            "groupname_regex": {
                "type": "string",
                "description": "Group name regex pattern. Examples: '^admin.*', '.*_group$'"
            },
            "inode": {
                "type": "integer",
                "description": "Specific inode number to find"
            },
            
            # File size and links
            "size": {
                "type": "string",
                "description": "File size filter. Examples: '100' (exact), '10M-2G' (range), '>1GB', '<=500MB', 'eq:100KB', 'gt:1MB'"
            },
            "nlinks": {
                "type": "string", 
                "description": "Hard link count filter. Examples: '1' (exact), '2-5' (range), 'gte:3', 'lt:10'"
            },
            
            # Case-insensitive versions
            "iname": {
                "type": "string",
                "description": "Case-insensitive filename pattern. Examples: 'CONFIG.json', 'readme.*'"
            },
            "iusername": {
                "type": "string",
                "description": "Case-insensitive username match. Examples: 'ADMIN', 'John'"
            },
            "igroupname": {
                "type": "string",
                "description": "Case-insensitive group name match. Examples: 'WHEEL', 'Users'"
            },
            
            # Directory depth
            "depth": {
                "type": "integer",
                "description": "Exact directory depth from search root (0=root level, 1=immediate children)"
            },
            "maxdepth": {
                "type": "integer",
                "description": "Maximum directory depth to search (limits recursion)"
            },
            
            # Permissions
            "perm": {
                "type": "string",
                "description": "Permission matching. Examples: '644' (exact), '-u=r' (at least user read), '/222' (any write)"
            },
            
            # Time filters
            "mtime": {
                "type": "string",
                "description": "Modification time. Examples: '-1d' (within 1 day), '2024-01-01' (since date), '1-7d' (1-7 days ago)"
            },
            "ctime": {
                "type": "string",
                "description": "Change time (metadata). Examples: '-2h' (within 2 hours), '2024-01-01-2024-02-01' (date range)"
            },
            "atime": {
                "type": "string",
                "description": "Access time. Examples: '+30d' (older than 30 days), 'inf-1w' (older than 1 week)"
            },
            
            # Query options
            "search_all": {
                "type": "boolean",
                "description": "Search all history versions, not just current files"
            },
            "versions": {
                "type": "boolean", 
                "description": "Show all historical versions of matching entries"
            },
            "children_only": {
                "type": "boolean",
                "description": "Return only immediate children of specified path (optimization)"
            },
            "root_only": {
                "type": "boolean",
                "description": "Return only the exact entry specified by path (optimization)"
            },
            
            # Tags
            "tag": {
                "type": "string",
                "description": "Tag search with AND/OR/NOT logic. Examples: 'important', 'tag1 tag2' (AND), multiple calls for OR"
            },
            "tag_explicit": {
                "type": "string",
                "description": "Tags attached directly (not inherited). Supports AND/OR/NOT logic"
            },
            
            # Search scope
            "volumes_and_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Limit search to specific volume:path combinations. Examples: ['home:', 'data:/projects']"
            },
            "zone": {
                "type": "string",
                "description": "Search within a specific zone name"
            },
            
            # Output control
            "limit": {
                "type": "integer",
                "default": 100,
                "description": "Maximum number of results to return"
            },
            "sort_by": {
                "type": "string",
                "description": "Sort by fields. Examples: 'size', '-mtime', '+parent_path,size'"
            },
            "format_fields": {
                "type": "string",
                "description": "Space-separated fields to include. Default includes all common fields"
            },
            
            # Performance
            "use_async": {
                "type": "boolean",
                "default": False,
                "description": "Use async query API for better performance on large searches"
            }
        },
        "additionalProperties": False
    }
