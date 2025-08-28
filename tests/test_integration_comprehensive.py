"""Comprehensive integration tests for new Starfish query parameters.

These tests require a real Starfish instance and should be run separately
from unit tests. Set the following environment variables to run:

- STARFISH_INTEGRATION_BASE_URL=https://your-starfish-instance.com/api
- STARFISH_INTEGRATION_USERNAME=your_username  
- STARFISH_INTEGRATION_PASSWORD=your_password

Run with: pytest tests/test_integration_comprehensive.py -v
"""

import pytest
import os
import json
from starfish_mcp.config import StarfishConfig
from starfish_mcp.client import StarfishClient
from starfish_mcp.tools import StarfishTools


@pytest.fixture
async def integration_tools():
    """Create tools instance for integration testing."""
    base_url = os.getenv("STARFISH_INTEGRATION_BASE_URL")
    username = os.getenv("STARFISH_INTEGRATION_USERNAME") 
    password = os.getenv("STARFISH_INTEGRATION_PASSWORD")
    
    if not all([base_url, username, password]):
        pytest.skip("Integration test environment variables not set")
    
    config = StarfishConfig(
        base_url=base_url,
        username=username,
        password=password,
        token_timeout_secs=57600
    )
    
    client = StarfishClient(config)
    tools = StarfishTools(client)
    
    # Test basic connectivity
    try:
        await client.list_volumes()
    except Exception as e:
        pytest.skip(f"Cannot connect to Starfish instance: {e}")
    
    return tools


@pytest.mark.asyncio
@pytest.mark.integration
async def test_basic_file_search(integration_tools):
    """Test basic file search functionality."""
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    assert "query" in data
    assert "results" in data
    assert data["query"] == "type=f"
    assert len(data["results"]) <= 5
    
    # Check result structure
    if data["results"]:
        file_result = data["results"][0]
        assert "filename" in file_result
        assert "full_path" in file_result
        assert "size" in file_result
        assert file_result["type"] == "file"


@pytest.mark.asyncio
@pytest.mark.integration 
async def test_size_filters(integration_tools):
    """Test size filter functionality."""
    # Test files larger than 1KB
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "size": ">1KB",
        "limit": 3
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    assert "size=>1KB" in data["query"]
    
    # Verify all returned files are larger than 1KB
    for file_result in data["results"]:
        # Size should be > 1024 bytes (1KB)
        assert file_result["size"] > 1024


@pytest.mark.asyncio
@pytest.mark.integration
async def test_file_extension_filter(integration_tools):
    """Test file extension filtering."""
    # Look for common file extensions
    extensions_to_test = ["txt", "log", "json", "py"]
    
    for ext in extensions_to_test:
        result = await integration_tools.handle_tool_call("starfish_query", {
            "file_type": "f",
            "ext": ext,
            "limit": 2
        })
        
        assert not result.isError
        data = json.loads(result.content[0].text)
        
        assert f"ext={ext}" in data["query"]
        
        # If files are found, verify they have the correct extension
        for file_result in data["results"]:
            filename = file_result["filename"]
            assert filename.endswith(f".{ext}"), f"File {filename} doesn't end with .{ext}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_directory_search(integration_tools):
    """Test directory-specific searches."""
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "d",
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    assert "type=d" in data["query"]
    
    # Verify all results are directories
    for dir_result in data["results"]:
        assert dir_result["type"] == "directory"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_depth_filters(integration_tools):
    """Test directory depth filtering."""
    # Test specific depth
    result = await integration_tools.handle_tool_call("starfish_query", {
        "depth": 1,
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "depth=1" in data["query"]
    
    # Test max depth
    result = await integration_tools.handle_tool_call("starfish_query", {
        "maxdepth": 2,
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert "maxdepth=2" in data["query"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_case_insensitive_search(integration_tools):
    """Test case-insensitive filename search."""
    # Look for common patterns that might exist in different cases
    patterns_to_test = ["readme.*", "config.*", "log.*"]
    
    for pattern in patterns_to_test:
        result = await integration_tools.handle_tool_call("starfish_query", {
            "iname": pattern,
            "file_type": "f",
            "limit": 3
        })
        
        assert not result.isError
        data = json.loads(result.content[0].text)
        
        assert f"iname={pattern}" in data["query"]
        
        # Files should match the pattern regardless of case
        for file_result in data["results"]:
            filename = file_result["filename"].lower()
            # Convert shell pattern to check
            if pattern == "readme.*":
                assert filename.startswith("readme")
            elif pattern == "config.*":
                assert filename.startswith("config")
            elif pattern == "log.*":
                assert filename.startswith("log")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_ownership_filters(integration_tools):
    """Test user ownership filtering."""
    # First, find what users exist by doing a general search
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "limit": 10
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    if not data["results"]:
        pytest.skip("No files found for ownership testing")
    
    # Get a UID that exists
    test_uid = data["results"][0]["uid"]
    
    # Test UID filtering
    result = await integration_tools.handle_tool_call("starfish_query", {
        "uid": test_uid,
        "file_type": "f",
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    assert f"uid={test_uid}" in data["query"]
    
    # Verify all results have the correct UID
    for file_result in data["results"]:
        assert file_result["uid"] == test_uid


@pytest.mark.asyncio
@pytest.mark.integration
async def test_combined_filters(integration_tools):
    """Test multiple filters combined."""
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "size": ">0",      # Non-empty files
        "maxdepth": 3,     # Not too deep
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    query = data["query"]
    assert "type=f" in query
    assert "size=>0" in query
    assert "maxdepth=3" in query
    
    # Verify results match all criteria
    for file_result in data["results"]:
        assert file_result["type"] == "file"
        assert file_result["size"] > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_all_flag(integration_tools):
    """Test search-all flag for historical data."""
    # Compare regular search vs search-all
    regular_result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "limit": 5
    })
    
    search_all_result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "search_all": True,
        "limit": 5
    })
    
    assert not regular_result.isError
    assert not search_all_result.isError
    
    regular_data = json.loads(regular_result.content[0].text)
    search_all_data = json.loads(search_all_result.content[0].text)
    
    # search-all query should include the flag
    assert "search-all" in search_all_data["query"]
    assert "search-all" not in regular_data["query"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_query_performance(integration_tools):
    """Test async query for performance on larger searches."""
    # Test sync vs async query (if volumes exist)
    volumes_result = await integration_tools.handle_tool_call("starfish_list_volumes", {})
    volumes_data = json.loads(volumes_result.content[0].text)
    
    if not volumes_data["volumes"]:
        pytest.skip("No volumes available for async testing")
    
    # Get first volume name
    volume_name = volumes_data["volumes"][0]["name"]
    
    # Test async query
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "volumes_and_paths": [f"{volume_name}:"],
        "use_async": True,
        "limit": 10
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    assert data["use_async"] is True
    assert data["search_scope"] == [f"{volume_name}:"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_volume_scoped_search(integration_tools):
    """Test searching within specific volumes."""
    # Get available volumes
    volumes_result = await integration_tools.handle_tool_call("starfish_list_volumes", {})
    volumes_data = json.loads(volumes_result.content[0].text)
    
    if not volumes_data["volumes"]:
        pytest.skip("No volumes available for scoped testing")
    
    volume_name = volumes_data["volumes"][0]["name"]
    
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "volumes_and_paths": [f"{volume_name}:"],
        "limit": 5
    })
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    assert data["search_scope"] == [f"{volume_name}:"]
    
    # All results should be from the specified volume
    for file_result in data["results"]:
        assert file_result["volume"] == volume_name


@pytest.mark.asyncio
@pytest.mark.integration
async def test_management_tools(integration_tools):
    """Test management tools (volumes, zones, tagsets)."""
    # Test list volumes
    volumes_result = await integration_tools.handle_tool_call("starfish_list_volumes", {})
    assert not volumes_result.isError
    
    volumes_data = json.loads(volumes_result.content[0].text)
    assert "volumes" in volumes_data
    assert "total_volumes" in volumes_data
    
    # Test list zones
    zones_result = await integration_tools.handle_tool_call("starfish_list_zones", {})
    assert not zones_result.isError
    
    zones_data = json.loads(zones_result.content[0].text)
    assert "zones" in zones_data
    assert "total_zones" in zones_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_handling(integration_tools):
    """Test error handling with invalid queries."""
    # Test with invalid file type
    result = await integration_tools.handle_tool_call("starfish_query", {
        "file_type": "invalid_type"
    })
    
    # Should handle the error gracefully
    # (Note: This might succeed if Starfish accepts the invalid type,
    # or fail gracefully if it doesn't)
    if result.isError:
        assert "error" in result.content[0].text.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_query_building_accuracy(integration_tools):
    """Test that complex queries are built correctly."""
    complex_args = {
        "name": "*.log",
        "file_type": "f",
        "size": ">1KB", 
        "maxdepth": 2,
        "limit": 3
    }
    
    result = await integration_tools.handle_tool_call("starfish_query", complex_args)
    
    assert not result.isError
    data = json.loads(result.content[0].text)
    
    # Verify query construction
    query = data["query"]
    assert "name=*.log" in query
    assert "type=f" in query
    assert "size=>1KB" in query
    assert "maxdepth=2" in query
    
    # Verify metadata matches input
    filters = data["filters_applied"]
    assert filters["name"] == "*.log"
    assert filters["file_type"] == "f"
    assert filters["size"] == ">1KB"
    assert filters["maxdepth"] == 2
