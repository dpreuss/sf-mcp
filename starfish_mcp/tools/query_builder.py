"""Starfish query string builder from parameters."""

from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


def build_starfish_query(arguments: Dict[str, Any]) -> str:
    """Build Starfish query string from tool arguments."""
    # Extract parameters
    name = arguments.get("name")
    name_regex = arguments.get("name_regex")
    path = arguments.get("path")
    path_regex = arguments.get("path_regex")
    file_type = arguments.get("file_type")
    ext = arguments.get("ext")
    empty = arguments.get("empty")
    uid = arguments.get("uid")
    gid = arguments.get("gid")
    username = arguments.get("username")
    username_regex = arguments.get("username_regex")
    groupname = arguments.get("groupname")
    groupname_regex = arguments.get("groupname_regex")
    inode = arguments.get("inode")
    size = arguments.get("size")
    nlinks = arguments.get("nlinks")
    iname = arguments.get("iname")
    iusername = arguments.get("iusername")
    igroupname = arguments.get("igroupname")
    depth = arguments.get("depth")
    maxdepth = arguments.get("maxdepth")
    perm = arguments.get("perm")
    mtime = arguments.get("mtime")
    ctime = arguments.get("ctime")
    atime = arguments.get("atime")
    search_all = arguments.get("search_all")
    versions = arguments.get("versions")
    children_only = arguments.get("children_only")
    root_only = arguments.get("root_only")
    tag = arguments.get("tag")
    tag_explicit = arguments.get("tag_explicit")
    zone = arguments.get("zone")
    
    # Build query parts
    query_parts = []
    
    # File type
    if file_type:
        query_parts.append(f"type={file_type}")
    
    # Names and paths
    if name:
        # Check if it's a regex pattern (starts with ^ or contains regex chars)
        if name.startswith('^') or any(c in name for c in ['(', ')', '[', ']', '{', '}', '|', '+', '?']):
            if not name.startswith('^'):
                name = '^' + name
            query_parts.append(f"name-re={name}")
        elif '*' in name or '?' in name:
            # Shell pattern
            query_parts.append(f"name={name}")
        else:
            # Exact match for alphanumeric
            query_parts.append(f"name={name}")
    
    if name_regex:
        if not name_regex.startswith('^'):
            name_regex = '^' + name_regex
        query_parts.append(f"name-re={name_regex}")
    
    if path:
        query_parts.append(f"ppath={path}")
    
    if path_regex:
        if not path_regex.startswith('^'):
            path_regex = '^' + path_regex
        query_parts.append(f"ppath-re={path_regex}")
    
    # File attributes
    if ext:
        query_parts.append(f"ext={ext}")
    
    if empty is not None:
        if empty:
            query_parts.append("empty")
    
    if inode:
        query_parts.append(f"inode={inode}")
    
    # Ownership
    if uid is not None:
        query_parts.append(f"uid={uid}")
    
    if gid is not None:
        query_parts.append(f"gid={gid}")
    
    if username:
        query_parts.append(f"username={username}")
    
    if username_regex:
        if not username_regex.startswith('^'):
            username_regex = '^' + username_regex
        query_parts.append(f"username-re={username_regex}")
    
    if groupname:
        query_parts.append(f"groupname={groupname}")
    
    if groupname_regex:
        if not groupname_regex.startswith('^'):
            groupname_regex = '^' + groupname_regex
        query_parts.append(f"groupname-re={groupname_regex}")
    
    # Size and links
    if size:
        query_parts.append(f"size={size}")
    
    if nlinks:
        query_parts.append(f"nlinks={nlinks}")
    
    # Case-insensitive versions
    if iname:
        query_parts.append(f"iname={iname}")
    
    if iusername:
        query_parts.append(f"iusername={iusername}")
    
    if igroupname:
        query_parts.append(f"igroupname={igroupname}")
    
    # Depth
    if depth is not None:
        query_parts.append(f"depth={depth}")
    
    if maxdepth is not None:
        query_parts.append(f"maxdepth={maxdepth}")
    
    # Permissions
    if perm:
        query_parts.append(f"perm={perm}")
    
    # Time filters
    if mtime:
        query_parts.append(f"mtime={mtime}")
    
    if ctime:
        query_parts.append(f"ctime={ctime}")
    
    if atime:
        query_parts.append(f"atime={atime}")
    
    # Query options
    if search_all:
        query_parts.append("search-all")
    
    if versions:
        query_parts.append("versions")
    
    if children_only:
        query_parts.append("children-only")
    
    if root_only:
        query_parts.append("root-only")
    
    # Tags
    if tag:
        query_parts.append(f"tag={tag}")
    
    if tag_explicit:
        query_parts.append(f"tag-explicit={tag_explicit}")
    
    # Zone
    if zone:
        query_parts.append(f"zone={zone}")
    
    query = " ".join(query_parts)
    
    logger.debug("Built Starfish query", query=query, total_parts=len(query_parts))
    return query


def extract_query_metadata(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata about applied filters for result output."""
    return {
        "name": arguments.get("name"),
        "name_regex": arguments.get("name_regex"),
        "path": arguments.get("path"),
        "path_regex": arguments.get("path_regex"),
        "file_type": arguments.get("file_type"),
        "ext": arguments.get("ext"),
        "empty": arguments.get("empty"),
        "uid": arguments.get("uid"),
        "gid": arguments.get("gid"),
        "username": arguments.get("username"),
        "username_regex": arguments.get("username_regex"),
        "groupname": arguments.get("groupname"),
        "groupname_regex": arguments.get("groupname_regex"),
        "inode": arguments.get("inode"),
        "size": arguments.get("size"),
        "nlinks": arguments.get("nlinks"),
        "iname": arguments.get("iname"),
        "iusername": arguments.get("iusername"),
        "igroupname": arguments.get("igroupname"),
        "depth": arguments.get("depth"),
        "maxdepth": arguments.get("maxdepth"),
        "perm": arguments.get("perm"),
        "mtime": arguments.get("mtime"),
        "ctime": arguments.get("ctime"),
        "atime": arguments.get("atime"),
        "search_all": arguments.get("search_all"),
        "versions": arguments.get("versions"),
        "children_only": arguments.get("children_only"),
        "root_only": arguments.get("root_only"),
        "tag": arguments.get("tag"),
        "tag_explicit": arguments.get("tag_explicit"),
        "zone": arguments.get("zone")
    }
