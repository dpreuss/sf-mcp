"""Tests for Starfish data models."""

import pytest
from datetime import datetime
from starfish_mcp.models import StarfishEntry, VolumeInfo, StarfishQueryResponse, StarfishTagsResponse


def test_starfish_entry_basic_properties():
    """Test basic StarfishEntry properties."""
    entry_data = {
        "_id": 12345,
        "fn": "test_file.txt",
        "parent_path": "/data",
        "type": 32768,
        "size": 1024,
        "volume": "storage1",
        "mt": 1640995200,  # 2022-01-01 00:00:00 UTC
        "ct": 1640995100,  # 2022-01-01 00:01:40 UTC
        "at": 1640995300,  # 2022-01-01 00:01:40 UTC
        "tags_explicit": "tag1,tag2,tag3",
        "tags_inherited": "inherited1,inherited2"
    }
    
    entry = StarfishEntry(**entry_data)
    
    assert entry.id == 12345
    assert entry.filename == "test_file.txt"
    assert entry.parent_path == "/data"
    assert entry.type == 32768
    assert entry.size == 1024
    assert entry.volume == "storage1"
    assert entry.is_file is True


def test_starfish_entry_time_properties():
    """Test StarfishEntry time conversion properties."""
    entry_data = {
        "_id": 12345,
        "fn": "test_file.txt",
        "type": 32768,
        "size": 1024,
        "volume": "storage1",
        "mt": 1640995200,  # 2022-01-01 00:00:00 UTC
        "ct": 1640995100,  # 2021-12-31 23:58:20 UTC
        "at": 1640995300,  # 2022-01-01 00:01:40 UTC
    }
    
    entry = StarfishEntry(**entry_data)
    
    assert entry.modify_time == datetime.fromtimestamp(1640995200)
    assert entry.create_time == datetime.fromtimestamp(1640995100)
    assert entry.access_time == datetime.fromtimestamp(1640995300)


def test_starfish_entry_tags_properties():
    """Test StarfishEntry tag parsing properties."""
    entry_data = {
        "_id": 12345,
        "fn": "test_file.txt",
        "type": 32768,
        "size": 1024,
        "volume": "storage1",
        "tags_explicit": "tag1,tag2,tag3",
        "tags_inherited": "inherited1,inherited2"
    }
    
    entry = StarfishEntry(**entry_data)
    
    assert entry.tags_explicit == ["tag1", "tag2", "tag3"]
    assert entry.tags_inherited == ["inherited1", "inherited2"]
    assert entry.all_tags == ["tag1", "tag2", "tag3", "inherited1", "inherited2"]


def test_starfish_entry_empty_tags():
    """Test StarfishEntry with empty or None tags."""
    entry_data = {
        "_id": 12345,
        "fn": "test_file.txt",
        "type": 32768,
        "size": 1024,
        "volume": "storage1",
    }
    
    entry = StarfishEntry(**entry_data)
    
    assert entry.tags_explicit == []
    assert entry.tags_inherited == []
    assert entry.all_tags == []


def test_starfish_entry_whitespace_tags():
    """Test StarfishEntry tag parsing with whitespace."""
    entry_data = {
        "_id": 12345,
        "fn": "test_file.txt",
        "type": 32768,
        "size": 1024,
        "volume": "storage1",
        "tags_explicit": " tag1 , tag2 , , tag3 ",
        "tags_inherited": "inherited1,  ,inherited2"
    }
    
    entry = StarfishEntry(**entry_data)
    
    assert entry.tags_explicit == ["tag1", "tag2", "tag3"]
    assert entry.tags_inherited == ["inherited1", "inherited2"]


def test_starfish_entry_directory_type():
    """Test StarfishEntry with directory type."""
    entry_data = {
        "_id": 12345,
        "fn": "test_dir",
        "type": 16384,  # Directory type
        "size": 4096,
        "volume": "storage1",
    }
    
    entry = StarfishEntry(**entry_data)
    
    assert entry.is_file is False


def test_volume_info():
    """Test VolumeInfo model."""
    volume_data = {
        "id": 1,
        "vol": "storage1",
        "display_name": "Primary Storage",
        "default_agent_address": "agent1.example.com",
        "mounts": {
            "agent1.example.com": "/mnt/storage1",
            "agent2.example.com": "/mnt/storage1"
        },
        "mount_opts": {
            "agent1.example.com": "rw,sync",
            "agent2.example.com": "rw,sync"
        },
        "type": "Linux"
    }
    
    volume = VolumeInfo(**volume_data)
    
    assert volume.id == 1
    assert volume.vol == "storage1"
    assert volume.display_name == "Primary Storage"
    assert volume.type == "Linux"
    assert volume.default_agent_address == "agent1.example.com"
    assert "agent1.example.com" in volume.mounts
    assert volume.mounts["agent1.example.com"] == "/mnt/storage1"


def test_starfish_query_response():
    """Test StarfishQueryResponse (direct array) model."""
    entry_data = {
        "_id": 12345,
        "fn": "test_file.txt",
        "type": 32768,
        "size": 1024,
        "volume": "storage1",
    }
    
    # The API returns an array directly, not wrapped in an object
    response_data = [entry_data]
    
    # Validate that we can parse individual entries
    from starfish_mcp.models import StarfishEntry
    entries = [StarfishEntry(**item) for item in response_data]
    
    assert len(entries) == 1
    assert entries[0].filename == "test_file.txt"


def test_starfish_tags_response():
    """Test StarfishTagsResponse model."""
    tags_data = {
        "tags": ["tag1", "tag2", "tagset1:tag3", ":default_tag"]
    }
    
    response = StarfishTagsResponse(**tags_data)
    
    assert len(response.tags) == 4
    assert "tag1" in response.tags
    assert "tagset1:tag3" in response.tags
    assert ":default_tag" in response.tags
