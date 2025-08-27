"""Data models for Starfish API responses."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SizeUnit(str, Enum):
    """Allowed size units for Starfish API."""
    B = "B"
    KB = "KB" 
    KiB = "KiB"
    MB = "MB"
    MiB = "MiB"
    GB = "GB"
    GiB = "GiB"
    TB = "TB"
    TiB = "TiB"


class StarfishEntry(BaseModel):
    """Represents a single file/directory entry from Starfish API response."""
    
    id: int = Field(..., alias="_id", description="Starfish entry ID")
    filename: str = Field(..., alias="fn", description="File/directory name")
    parent_path: Optional[str] = Field(None, alias="parent_path", description="Parent directory path")
    full_path: Optional[str] = Field(None, alias="full_path", description="Full file path")
    type: int = Field(..., description="Entry type (32768 for file, other for directory)")
    size: int = Field(..., description="File size in bytes")
    mode: Optional[str] = Field(None, description="File mode/permissions")
    uid: Optional[int] = Field(None, description="User ID")
    gid: Optional[int] = Field(None, description="Group ID")
    create_time_unix: Optional[int] = Field(None, alias="ct", description="Creation time (Unix timestamp)")
    modify_time_unix: Optional[int] = Field(None, alias="mt", description="Modification time (Unix timestamp)")
    access_time_unix: Optional[int] = Field(None, alias="at", description="Access time (Unix timestamp)")
    volume: str = Field(..., description="Volume name")
    inode: Optional[int] = Field(None, alias="ino", description="Inode number")
    size_unit: Optional[SizeUnit] = Field(None, alias="size_unit", description="Size unit")
    tags_explicit_str: Optional[str] = Field(None, alias="tags_explicit", description="Explicit tags (comma-separated)")
    tags_inherited_str: Optional[str] = Field(None, alias="tags_inherited", description="Inherited tags (comma-separated)")
    zones: Optional[List["StarfishZone"]] = Field(None, description="Zone information")
    
    model_config = {"populate_by_name": True}
    
    @property
    def is_file(self) -> bool:
        """Check if entry is a file (type 32768)."""
        return self.type == 32768
    
    @property
    def create_time(self) -> Optional[datetime]:
        """Get creation time as datetime object."""
        if self.create_time_unix:
            return datetime.fromtimestamp(self.create_time_unix)
        return None
    
    @property
    def modify_time(self) -> Optional[datetime]:
        """Get modification time as datetime object."""
        if self.modify_time_unix:
            return datetime.fromtimestamp(self.modify_time_unix)
        return None
    
    @property
    def access_time(self) -> Optional[datetime]:
        """Get access time as datetime object."""
        if self.access_time_unix:
            return datetime.fromtimestamp(self.access_time_unix)
        return None
    
    @property
    def tags_explicit(self) -> List[str]:
        """Get explicit tags as list."""
        if self.tags_explicit_str:
            return [tag.strip() for tag in self.tags_explicit_str.split(",") if tag.strip()]
        return []
    
    @property
    def tags_inherited(self) -> List[str]:
        """Get inherited tags as list."""
        if self.tags_inherited_str:
            return [tag.strip() for tag in self.tags_inherited_str.split(",") if tag.strip()]
        return []
    
    @property
    def all_tags(self) -> List[str]:
        """Get all tags (explicit + inherited) as list."""
        return self.tags_explicit + self.tags_inherited


class StarfishGroupedResult(BaseModel):
    """Represents grouped query results when group_by parameter is used."""
    
    count: int = Field(..., description="Number of grouped entries")
    size_sum: int = Field(..., description="Sum of grouped entries size")
    size_sum_hum: Optional[str] = Field(None, description="Humanized version of size_sum")
    # Dynamic fields based on group_by parameter
    extra_fields: Dict[str, Any] = Field(default_factory=dict, description="Additional grouping fields")
    
    model_config = {"populate_by_name": True, "extra": "allow"}


class StarfishZone(BaseModel):
    """Represents zone information from Starfish."""
    
    id: int = Field(..., description="Zone ID")
    name: str = Field(..., description="Zone name")
    relative_path: str = Field(..., description="Relative path within zone")


class StarfishZoneManager(BaseModel):
    """Zone manager information."""
    
    system_id: Union[int, str] = Field(..., description="System ID of the manager (UID - integer or string)")
    username: str = Field(..., description="Username of the manager")


class StarfishZoneGroup(BaseModel):
    """Zone managing group information."""
    
    system_id: Union[int, str] = Field(..., description="System ID of the group (GID - integer or string)")
    groupname: str = Field(..., description="Group name")


class StarfishZoneTagset(BaseModel):
    """Zone tagset information."""
    
    name: str = Field(..., description="Tagset name")
    tag_names: List[str] = Field(..., description="List of tag names in the tagset")


class StarfishZoneAggregates(BaseModel):
    """Zone aggregation statistics."""
    
    size: Optional[int] = Field(None, description="Total size in bytes")
    dirs: Optional[int] = Field(None, description="Number of directories")
    files: Optional[int] = Field(None, description="Number of files") 
    cost: Optional[float] = Field(None, description="Cost associated with the zone")


class StarfishZoneDetails(BaseModel):
    """Detailed zone information from Starfish API."""
    
    id: int = Field(..., description="Zone ID")
    name: str = Field(..., description="Zone name")
    managers: List[StarfishZoneManager] = Field(default_factory=list, description="Zone managers")
    managing_groups: List[StarfishZoneGroup] = Field(default_factory=list, description="Managing groups")
    restore_managers: List[str] = Field(default_factory=list, description="Restore managers names")
    restore_managing_groups: List[str] = Field(default_factory=list, description="Restore managing group names")
    paths: List[str] = Field(default_factory=list, description="Zone paths (volume:path format)")
    tagsets: List[StarfishZoneTagset] = Field(default_factory=list, description="Zone tagsets")
    user_params: Dict[str, Any] = Field(default_factory=dict, description="User-defined parameters")
    aggregates: Optional[StarfishZoneAggregates] = Field(None, description="Zone statistics")


# The query API returns an array directly, so we'll use Union type for individual results
StarfishQueryResult = Union[StarfishEntry, StarfishGroupedResult]
StarfishQueryResponse = List[StarfishQueryResult]


class VolumeSizeInfo(BaseModel):
    """Volume size usage information."""
    
    number_of_files: Optional[int] = Field(None, description="Number of files")
    number_of_dirs: Optional[int] = Field(None, description="Number of directories")
    sum_of_logical_sizes_div_nlinks: Optional[int] = Field(None, description="Logical size divided by nlinks")
    sum_of_logical_sizes_no_nlinks: Optional[int] = Field(None, description="Sum of logical sizes")
    sum_of_physical_sizes_div_nlinks: Optional[int] = Field(None, description="Physical size divided by nlinks")
    sum_of_blocks_div_nlinks: Optional[int] = Field(None, description="Blocks divided by nlinks")
    sum_of_physical_sizes_no_nlinks: Optional[int] = Field(None, description="Sum of physical sizes")
    sum_of_blocks: Optional[int] = Field(None, description="Number of blocks used")
    # Deprecated fields
    sum_of_logical_sizes: Optional[int] = Field(None, description="Deprecated: same as sum_of_logical_sizes_no_nlinks")
    sum_of_physical_sizes: Optional[int] = Field(None, description="Deprecated: same as sum_of_physical_sizes_div_nlinks")


class VolumeInfo(BaseModel):
    """Volume information from Starfish API."""
    
    # Core identification
    id: int = Field(..., description="Numerical ID of volume")
    vol: str = Field(..., description="Volume name")
    display_name: Optional[str] = Field(None, description="User-friendly display name")
    
    # Agent and mounting
    default_agent_address: str = Field(..., description="Default agent for scanning")
    mounts: Dict[str, str] = Field(default_factory=dict, description="Map of agent address to mount points")
    mount_opts: Dict[str, Optional[str]] = Field(default_factory=dict, description="Map of agent address to mount options")
    root: Optional[str] = Field(None, description="Path where volume is mounted on agent")
    
    # Exclusion patterns
    dir_excludes: List[str] = Field(default_factory=list, description="Directory exclusion patterns")
    file_excludes: List[str] = Field(default_factory=list, description="File exclusion patterns")
    
    # Stat field ignoring
    ignored_dir_stat_fields: List[str] = Field(default_factory=list, description="Ignored stat fields for directories")
    ignored_file_stat_fields: List[str] = Field(default_factory=list, description="Ignored stat fields for files")
    
    # Windows-specific settings
    store_win_acl: Optional[bool] = Field(True, description="Store Windows ACLs (Windows volumes only)")
    store_win_attr: Optional[bool] = Field(False, description="Store Windows attributes (Windows volumes only)")
    
    # POSIX settings
    store_posix_acl: Optional[bool] = Field(False, description="Store POSIX ACLs")
    
    # Extended attributes
    store_xattrs: Optional[bool] = Field(False, description="Store extended attributes")
    store_xattrs_regex: Optional[str] = Field(None, description="Regex pattern for extended attributes")
    
    # Capacity management
    total_capacity: Optional[float] = Field(None, description="Volume capacity")
    capacity_set_manually: Optional[bool] = Field(None, description="Whether capacity is set manually")
    free_space: Optional[float] = Field(None, description="Free space on volume")
    free_space_set_manually: Optional[bool] = Field(None, description="Whether free space is set manually")
    
    # Volume type and configuration
    type: str = Field(..., description="Volume type (Linux/Windows/virtual)")
    history_length: Optional[int] = Field(None, description="History pruning interval in seconds")
    prune_history_cut_off: Optional[str] = Field(None, description="History pruning cutoff date")
    
    # Service status
    cron_service_up: Optional[bool] = Field(None, description="Whether cron service is running")
    
    # Cost information
    cost_per_gb: Optional[float] = Field(None, description="Cost per GB")
    loaded_cost_per_gb: Optional[float] = Field(None, description="Loaded cost per GB")
    
    # Hardware information
    vendor: Optional[str] = Field(None, description="Storage vendor")
    model: Optional[str] = Field(None, description="Storage model")
    location: Optional[str] = Field(None, description="Physical location")
    tier: Optional[str] = Field(None, description="Storage tier")
    
    # Inode information
    inode: Optional[int] = Field(None, description="Inode number")
    inode_str: Optional[str] = Field(None, description="Inode as string for JS compatibility")
    
    # User parameters
    user_params: Dict[str, Any] = Field(default_factory=dict, description="User-defined parameters")
    
    # Agents configuration
    agents_with_scans_disabled: List[str] = Field(default_factory=list, description="Agents with disabled scans")
    
    # Optional detailed information (requires specific flags)
    cron: Optional[List[Dict[str, Any]]] = Field(None, description="Cron information (with add_cron_info=true)")
    volume_size_info: Optional[VolumeSizeInfo] = Field(None, description="Size usage info (with with_disk_usage=true)")
    
    # Additional statistics fields (also available at root level)
    number_of_files: Optional[int] = Field(None, description="Number of files")
    number_of_dirs: Optional[int] = Field(None, description="Number of directories")
    sum_of_logical_sizes_div_nlinks: Optional[int] = Field(None, description="Logical size divided by nlinks")
    sum_of_logical_sizes_no_nlinks: Optional[int] = Field(None, description="Sum of logical sizes")
    sum_of_physical_sizes_div_nlinks: Optional[int] = Field(None, description="Physical size divided by nlinks")
    sum_of_blocks_div_nlinks: Optional[int] = Field(None, description="Blocks divided by nlinks")
    sum_of_physical_sizes_no_nlinks: Optional[int] = Field(None, description="Sum of physical sizes")
    sum_of_blocks: Optional[int] = Field(None, description="Number of blocks used")
    sum_of_logical_sizes: Optional[int] = Field(None, description="Deprecated: same as sum_of_logical_sizes_no_nlinks")
    sum_of_physical_sizes: Optional[int] = Field(None, description="Deprecated: same as sum_of_physical_sizes_div_nlinks")
    
    model_config = {"populate_by_name": True}


class StarfishTagsResponse(BaseModel):
    """Response from tags API (GET /tag/)."""
    
    tags: List[str] = Field(..., description="List of tag names (may include tagset:tag format)")
    
    model_config = {"populate_by_name": True}


class StarfishTag(BaseModel):
    """Individual tag within a tagset."""
    
    id: int = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")


class TagsetAction(str, Enum):
    """Allowed tagset action types."""
    CLASSIFICATION = "CLASSIFICATION"
    MOVE = "MOVE" 
    COPY = "COPY"
    DELETE = "DELETE"


class StarfishTagsetResponse(BaseModel):
    """Response from single tagset API (GET /tagset/{tagset_name}/)."""
    
    name: str = Field(..., description="Tagset name")
    zone_ids: List[int] = Field(default_factory=list, description="Zone IDs associated with tagset")
    zones: List[StarfishZoneDetails] = Field(default_factory=list, description="Detailed zone information")
    inheritable: bool = Field(..., description="Whether tags should be displayed in tagged subtree")
    pinnable: bool = Field(..., description="Whether tags should be pinned when archiving")
    action: Optional[TagsetAction] = Field(None, description="Action type for this tagset")
    tags: List[StarfishTag] = Field(default_factory=list, description="Tags in this tagset")
    
    model_config = {"populate_by_name": True}


class StarfishAuthRequest(BaseModel):
    """Request model for Starfish authentication."""
    
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    token_timeout_secs: int = Field(57600, description="Token timeout in seconds (16 hours default)")
    token_description: str = Field("Starfish MCP Server", description="Token description")
    auto_generated: bool = Field(True, description="Whether token is auto-generated")


class StarfishAuthResponse(BaseModel):
    """Response model for Starfish authentication."""
    
    token: str = Field(..., description="Bearer token (format: sf-api-v1:token_id:token_secret)")
    expires_at: Optional[str] = Field(None, description="Token expiration time")


class StarfishError(Exception):
    """Starfish API error response."""
    
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# Update forward references
StarfishEntry.model_rebuild()
