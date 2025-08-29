"""Test configuration and fixtures."""

import pytest
import json
import os
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from starfish_mcp.config import StarfishConfig
from starfish_mcp.models import StarfishEntry, VolumeInfo, StarfishQueryResponse, StarfishZoneDetails


@pytest.fixture
def mock_config() -> StarfishConfig:
    """Mock configuration for testing."""
    return StarfishConfig(
        api_endpoint="https://mock-starfish.example.com/api",
        username="mock-user",
        password="mock-password",
        token_timeout_secs=57600,
        file_server_url="https://mock-fileserver.example.com",
        cache_ttl_hours=1,
        collections_refresh_interval_minutes=10,
        http_timeout_seconds=30,
        max_idle_connections=100,
        max_idle_connections_per_host=10,
        tls_insecure_skip_verify=False,
        tls_min_version="1.2",
        log_level="DEBUG"
    )


@pytest.fixture
def sample_starfish_entries() -> List[Dict[str, Any]]:
    """Sample Starfish entry data for testing."""
    base_time = int(datetime.now().timestamp())
    
    return [
        {
            "_id": 12345,
            "fn": "test_file.txt",
            "parent_path": "/data/projects",
            "full_path": "/data/projects/test_file.txt",
            "type": 32768,  # Regular file
            "size": 1024,
            "mode": "644",
            "uid": 1000,
            "gid": 1000,
            "ct": base_time - 86400,  # Created 1 day ago
            "mt": base_time - 3600,   # Modified 1 hour ago
            "at": base_time - 1800,   # Accessed 30 minutes ago
            "volume": "storage1",
            "ino": 123456,
            "tags_explicit": "project:alpha,status:active",
            "tags_inherited": "Collections:TestData,team:engineering",
            "zones": [
                {"id": 1, "name": "primary", "relative_path": "data/projects"}
            ]
        },
        {
            "_id": 12346,
            "fn": "foo.pdf",
            "parent_path": "/documents",
            "full_path": "/documents/foo.pdf",
            "type": 32768,
            "size": 2048576,  # 2MB
            "mode": "644",
            "uid": 1001,
            "gid": 1001,
            "ct": base_time - 172800,  # Created 2 days ago
            "mt": base_time - 7200,    # Modified 2 hours ago
            "at": base_time - 900,     # Accessed 15 minutes ago
            "volume": "storage2",
            "ino": 123457,
            "tags_explicit": "document:pdf,important",
            "tags_inherited": "Collections:Documents",
            "zones": [
                {"id": 2, "name": "archive", "relative_path": "documents"}
            ]
        },
        {
            "_id": 12347,
            "fn": "data.csv",
            "parent_path": "/baz",
            "full_path": "/baz/data.csv",
            "type": 32768,
            "size": 512000,
            "mode": "644",
            "uid": 1000,
            "gid": 1000,
            "ct": base_time - 259200,  # Created 3 days ago
            "mt": base_time - 10800,   # Modified 3 hours ago
            "at": base_time - 300,     # Accessed 5 minutes ago
            "volume": "storage1",
            "ino": 123458,
            "tags_explicit": "bar,data:csv",
            "tags_inherited": "Collections:Analytics",
        },
        {
            "_id": 12348,
            "fn": "config.json",
            "parent_path": "/baz/config",
            "full_path": "/baz/config/config.json",
            "type": 32768,
            "size": 4096,
            "mode": "600",
            "uid": 1000,
            "gid": 1000,
            "ct": base_time - 86400,
            "mt": base_time - 3600,
            "at": base_time - 60,
            "volume": "storage1",
            "ino": 123459,
            "tags_explicit": "config,bar",
            "tags_inherited": "Collections:Configuration",
        }
    ]


@pytest.fixture
def sample_volumes() -> List[Dict[str, Any]]:
    """Sample volume data for testing."""
    return [
        {
            "id": 1,
            "vol": "storage1",
            "display_name": "Primary Storage",
            "mounts": {
                "agent1.example.com": "/mnt/storage1",
                "agent2.example.com": "/mnt/storage1"
            },
            "mount_opts": {
                "agent1.example.com": "rw,sync",
                "agent2.example.com": "rw,sync"
            },
            "type": "nfs",
            "default_agent_address": "agent1.example.com",
            "root": "/mnt/storage1"
        },
        {
            "id": 2,
            "vol": "storage2",
            "display_name": "Archive Storage",
            "mounts": {
                "agent1.example.com": "/mnt/archive",
                "agent3.example.com": "/mnt/archive"
            },
            "mount_opts": {
                "agent1.example.com": "ro",
                "agent3.example.com": "ro"
            },
            "type": "nfs",
            "default_agent_address": "agent1.example.com",
            "root": "/mnt/archive"
        }
    ]


@pytest.fixture
def sample_collections() -> List[str]:
    """Sample collections (tag names) for testing."""
    return ["TestData", "Documents", "Analytics", "Configuration"]


@pytest.fixture
def sample_tagset_response() -> Dict[str, Any]:
    """Sample tagset response for testing."""
    return {
        "name": "Collections",
        "zone_ids": [1, 2],
        "inheritable": True,
        "pinnable": False,
        "action": "CLASSIFICATION",
        "tags": [
            {"id": 1, "name": "TestData"},
            {"id": 2, "name": "Documents"}, 
            {"id": 3, "name": "Analytics"},
            {"id": 4, "name": "Configuration"}
        ],
        "zones": []  # Will be populated with zone details if needed
    }


@pytest.fixture
def sample_zones() -> List[Dict[str, Any]]:
    """Sample zones data for testing."""
    return [
        {
            "id": 1,
            "name": "project_alpha",
            "managers": [
                {
                    "system_id": 1000,
                    "username": "alice"
                },
                {
                    "system_id": 1001,
                    "username": "bob"
                }
            ],
            "managing_groups": [
                {
                    "system_id": 100,
                    "groupname": "admins"
                }
            ],
            "restore_managers": ["alice", "bob"],
            "restore_managing_groups": ["admins"],
            "paths": ["storage1:/projects/alpha", "storage2:/backup/alpha"],
            "tagsets": [
                {
                    "name": "ProjectTags",
                    "tag_names": ["alpha", "active", "priority:high"]
                }
            ],
            "user_params": {
                "cost_per_gb": "0.05",
                "purpose": "Project Alpha development",
                "location": "datacenter-1"
            },
            "aggregates": {
                "size": 1073741824,  # 1GB
                "dirs": 25,
                "files": 150,
                "cost": 53.69
            }
        },
        {
            "id": 2,
            "name": "archive_zone",
            "managers": [
                {
                    "system_id": "1002",  # Test string system_id
                    "username": "charlie"
                }
            ],
            "managing_groups": [],
            "restore_managers": ["zone-managers"],
            "restore_managing_groups": [],
            "paths": ["storage3:/archive"],
            "tagsets": [
                {
                    "name": "ArchiveTags", 
                    "tag_names": ["archive", "readonly", "longterm"]
                }
            ],
            "user_params": {
                "cost_per_gb": "0.01",
                "purpose": "Long-term archive storage",
                "retention": "7years"
            },
            "aggregates": {
                "size": 5368709120,  # 5GB
                "dirs": 10,
                "files": 500,
                "cost": 26.84
            }
        }
    ]


class MockStarfishClient:
    """Mock Starfish client for testing."""
    
    def __init__(self, sample_entries: List[Dict[str, Any]], 
                 sample_volumes: List[Dict[str, Any]],
                 sample_collections: List[str],
                 sample_tagset_response: Dict[str, Any],
                 sample_zones: List[Dict[str, Any]]):
        self.sample_entries = sample_entries
        self.sample_volumes = sample_volumes
        self.sample_collections = sample_collections
        self.sample_tagset_response = sample_tagset_response
        self.sample_zones = sample_zones
        self.request_log: List[Dict[str, Any]] = []
        
    async def query(self, query: str, format_fields: str = None, 
                   limit: int = 1000, sort_by: str = None,
                   volumes_and_paths: str = None) -> List[StarfishEntry]:
        """Mock query method."""
        self.request_log.append({
            "method": "query",
            "query": query,
            "format_fields": format_fields,
            "limit": limit,
            "sort_by": sort_by,
            "volumes_and_paths": volumes_and_paths
        })
        
        # Filter entries based on query
        filtered_entries = self._filter_entries(query)
        
        return [StarfishEntry(**entry) for entry in filtered_entries]
    
    async def list_volumes(self) -> List[VolumeInfo]:
        """Mock list volumes method."""
        self.request_log.append({"method": "list_volumes"})
        return [VolumeInfo(**vol) for vol in self.sample_volumes]
    
    async def list_collections(self) -> List[str]:
        """Mock list collections method."""
        self.request_log.append({"method": "list_collections"})
        return self.sample_collections.copy()
    
    async def get_tagset(self, tagset_name: str, limit: int = 1000, 
                        with_private: bool = True) -> Dict[str, Any]:
        """Mock get tagset method."""
        self.request_log.append({
            "method": "get_tagset", 
            "tagset_name": tagset_name,
            "limit": limit,
            "with_private": with_private
        })
        return self.sample_tagset_response
    
    async def list_zones(self) -> List[StarfishZoneDetails]:
        """Mock list zones method."""
        self.request_log.append({"method": "list_zones"})
        return [StarfishZoneDetails(**zone) for zone in self.sample_zones]
    
    def _filter_entries(self, query: str) -> List[Dict[str, Any]]:
        """Filter entries based on query string."""
        if not query:
            return self.sample_entries.copy()
        
        filtered = []
        query_lower = query.lower()
        
        for entry in self.sample_entries:
            # Check filename match
            if "foo" in query_lower and "foo" in entry["fn"].lower():
                filtered.append(entry)
                continue
                
            # Check tag match
            if "tag=" in query_lower:
                tag_part = query_lower.split("tag=")[1].split()[0]
                all_tags = (entry.get("tags_explicit", "") + "," + 
                           entry.get("tags_inherited", "")).lower()
                if tag_part in all_tags:
                    filtered.append(entry)
                    continue
            
            # Check path match
            if "/baz" in query_lower and "/baz" in entry.get("parent_path", "").lower():
                filtered.append(entry)
                continue
                
            # Check type filter
            if "type=f" in query_lower and entry["type"] == 32768:
                filtered.append(entry)
                continue
        
        return filtered


@pytest.fixture
def mock_starfish_client(sample_starfish_entries, sample_volumes, 
                        sample_collections, sample_tagset_response, sample_zones) -> MockStarfishClient:
    """Create mock Starfish client."""
    return MockStarfishClient(
        sample_starfish_entries, 
        sample_volumes, 
        sample_collections,
        sample_tagset_response,
        sample_zones
    )


@pytest.fixture
def integration_config() -> StarfishConfig:
    """Configuration for integration tests (uses real Starfish if available)."""
    # Check if integration test environment variables are set
    api_endpoint = os.getenv("STARFISH_INTEGRATION_API_ENDPOINT")
    username = os.getenv("STARFISH_INTEGRATION_USERNAME")
    password = os.getenv("STARFISH_INTEGRATION_PASSWORD")
    
    if not api_endpoint or not username or not password:
        pytest.skip("Integration test environment not configured. "
                   "Set STARFISH_INTEGRATION_API_ENDPOINT, "
                   "STARFISH_INTEGRATION_USERNAME, and "
                   "STARFISH_INTEGRATION_PASSWORD to run integration tests.")
    
    return StarfishConfig(
        api_endpoint=api_endpoint,
        username=username,
        password=password,
        token_timeout_secs=int(os.getenv("STARFISH_INTEGRATION_TOKEN_TIMEOUT_SECS", "57600")),
        file_server_url=os.getenv("STARFISH_INTEGRATION_FILE_SERVER_URL"),
        cache_ttl_hours=1,
        collections_refresh_interval_minutes=10,
        http_timeout_seconds=60,  # Longer timeout for integration tests
        max_idle_connections=50,
        max_idle_connections_per_host=5,
        tls_insecure_skip_verify=os.getenv("STARFISH_INTEGRATION_TLS_SKIP_VERIFY", "false").lower() == "true",
        tls_min_version="1.2",
        log_level="DEBUG"
    )
