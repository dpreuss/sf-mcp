"""Tests for the new modular tools architecture."""

import pytest
import json
from unittest.mock import AsyncMock

from starfish_mcp.tools import StarfishTools
from starfish_mcp.tools.query_builder import build_starfish_query, extract_query_metadata
from starfish_mcp.tools.schema import get_starfish_query_schema
from starfish_mcp.models import StarfishError


def test_tools_creation(mock_starfish_client):
    """Test that tools can be created and list all expected tools."""
    tools = StarfishTools(mock_starfish_client)
    tool_list = tools.get_tools()
    
    assert len(tool_list) == 9
    
    # Check that expected tools are present
    tool_names = [tool.name for tool in tool_list]
    expected_tools = [
        "starfish_query",
        "starfish_list_volumes",
        "starfish_get_volume", 
        "starfish_list_zones",
        "starfish_get_zone",
        "starfish_get_tagset",
        "starfish_list_tagsets",
        "starfish_list_tags",
        "starfish_reset_query_count"
    ]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names
    
    # Check tool schema structure
    for tool in tool_list:
        assert tool.name is not None
        assert tool.description is not None
        assert tool.inputSchema is not None
        assert "type" in tool.inputSchema
        assert "properties" in tool.inputSchema


def test_starfish_query_schema():
    """Test the comprehensive starfish_query schema."""
    schema = get_starfish_query_schema()
    
    assert schema["type"] == "object"
    assert "properties" in schema
    
    properties = schema["properties"]
    
    # Test that all our implemented parameters are present
    expected_params = [
        # Basic search
        "name", "name_regex", "path", "path_regex", "file_type", "ext", "empty",
        # Ownership  
        "uid", "gid", "username", "username_regex", "groupname", "groupname_regex", "inode",
        # Size and links
        "size", "nlinks",
        # Case-insensitive
        "iname", "iusername", "igroupname", 
        # Depth
        "depth", "maxdepth",
        # Permissions
        "perm",
        # Time filters
        "mtime", "ctime", "atime",
        # Query options
        "search_all", "versions", "children_only", "root_only",
        # Tags
        "tag", "tag_explicit",
        # Scope
        "volumes_and_paths", "zone",
        # Output
        "limit", "sort_by", "format_fields", "use_async"
    ]
    
    for param in expected_params:
        assert param in properties, f"Parameter {param} missing from schema"
        assert "description" in properties[param], f"Parameter {param} missing description"
    
    # Test specific parameter types
    assert properties["uid"]["type"] == "integer"
    assert properties["empty"]["type"] == "boolean"
    assert properties["file_type"]["enum"] == ["f", "d", "l", "b", "c", "s", "p"]
    assert properties["volumes_and_paths"]["type"] == "array"


class TestQueryBuilder:
    """Test the query builder functionality."""
    
    def test_basic_query_building(self):
        """Test basic query parameter building."""
        args = {
            "name": "config.json",
            "file_type": "f",
            "ext": "json"
        }
        
        query = build_starfish_query(args)
        expected_parts = ["type=f", "name=config.json", "ext=json"]
        
        for part in expected_parts:
            assert part in query
    
    def test_size_and_nlinks_filters(self):
        """Test size and nlinks parameters."""
        args = {
            "size": ">10MB",
            "nlinks": "2-5",
            "file_type": "f"
        }
        
        query = build_starfish_query(args)
        assert "size=>10MB" in query
        assert "nlinks=2-5" in query
        assert "type=f" in query
    
    def test_case_insensitive_filters(self):
        """Test case-insensitive parameters."""
        args = {
            "iname": "CONFIG.*",
            "iusername": "ADMIN", 
            "igroupname": "WHEEL"
        }
        
        query = build_starfish_query(args)
        assert "iname=CONFIG.*" in query
        assert "iusername=ADMIN" in query
        assert "igroupname=WHEEL" in query
    
    def test_time_filters(self):
        """Test time filter parameters."""
        args = {
            "mtime": "-1d",
            "ctime": "-2h",
            "atime": "+30d"
        }
        
        query = build_starfish_query(args)
        assert "mtime=-1d" in query
        assert "ctime=-2h" in query
        assert "atime=+30d" in query
    
    def test_permission_filters(self):
        """Test permission filter parameters."""
        args = {
            "perm": "644"
        }
        
        query = build_starfish_query(args)
        assert "perm=644" in query
    
    def test_query_options(self):
        """Test query option flags."""
        args = {
            "search_all": True,
            "versions": True,
            "children_only": True,
            "root_only": False  # Should not appear
        }
        
        query = build_starfish_query(args)
        assert "search-all" in query
        assert "versions" in query
        assert "children-only" in query
        assert "root-only" not in query
    
    def test_regex_pattern_handling(self):
        """Test regex pattern processing."""
        # Name regex - should add ^ if missing
        args = {"name_regex": ".*\\.pdf$"}
        query = build_starfish_query(args)
        assert "name-re=^.*\\.pdf$" in query
        
        # Name regex - should preserve ^ if present
        args = {"name_regex": "^config.*"}
        query = build_starfish_query(args)
        assert "name-re=^config.*" in query
    
    def test_username_regex_pattern(self):
        """Test username regex pattern processing."""
        args = {"username_regex": "admin.*"}
        query = build_starfish_query(args)
        assert "username-re=^admin.*" in query
    
    def test_empty_query(self):
        """Test empty arguments."""
        args = {}
        query = build_starfish_query(args)
        assert query == ""
    
    def test_comprehensive_query(self):
        """Test a comprehensive query with many parameters."""
        args = {
            "name": "*.pdf",
            "file_type": "f",
            "size": ">1MB",
            "uid": 1001,
            "mtime": "-7d",
            "search_all": True,
            "limit": 100
        }
        
        query = build_starfish_query(args)
        expected_parts = [
            "type=f",
            "name=*.pdf", 
            "size=>1MB",
            "uid=1001",
            "mtime=-7d",
            "search-all"
        ]
        
        for part in expected_parts:
            assert part in query
    
    def test_extract_query_metadata(self):
        """Test metadata extraction for results."""
        args = {
            "name": "test.txt",
            "size": ">1MB",
            "uid": 1001,
            "search_all": True
        }
        
        metadata = extract_query_metadata(args)
        
        assert metadata["name"] == "test.txt"
        assert metadata["size"] == ">1MB"
        assert metadata["uid"] == 1001
        assert metadata["search_all"] is True
        assert metadata["gid"] is None  # Not provided


@pytest.mark.asyncio
async def test_starfish_query_tool(mock_starfish_client):
    """Test the comprehensive starfish_query tool."""
    tools = StarfishTools(mock_starfish_client)
    
    # Test with multiple parameters including our new ones
    result = await tools.handle_tool_call("starfish_query", {
        "name": "config.json",
        "file_type": "f",
        "size": ">1KB",
        "uid": 1001,
        "mtime": "-1d",
        "search_all": True,
        "limit": 10
    })
    
    # Parse JSON response from new dict format
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "query" in data
    assert "filters_applied" in data
    assert "results" in data
    assert "total_found" in data
    
    # Check that query was built correctly
    query = data["query"]
    assert "type=f" in query
    assert "name=config.json" in query
    assert "size=>1KB" in query
    assert "uid=1001" in query
    assert "mtime=-1d" in query
    assert "search-all" in query
    
    # Check filters_applied metadata
    filters = data["filters_applied"]
    assert filters["name"] == "config.json"
    assert filters["file_type"] == "f"
    assert filters["size"] == ">1KB"
    assert filters["uid"] == 1001
    assert filters["mtime"] == "-1d"
    assert filters["search_all"] is True


@pytest.mark.asyncio
async def test_time_filter_combinations(mock_starfish_client):
    """Test various time filter combinations."""
    tools = StarfishTools(mock_starfish_client)
    
    test_cases = [
        {"mtime": "-1d"},                    # Last day
        {"ctime": "-2h"},                    # Last 2 hours
        {"atime": "+30d"},                   # Older than 30 days
        {"mtime": "2024-01-01"},            # Since specific date
        {"mtime": "-1d", "atime": "+7d"},   # Combined filters
    ]
    
    for case in test_cases:
        result = await tools.handle_tool_call("starfish_query", case)
        data = json.loads(result["content"][0]["text"])
        query = data["query"]
        
        for key, value in case.items():
            assert f"{key}={value}" in query


@pytest.mark.asyncio
async def test_case_insensitive_filters(mock_starfish_client):
    """Test case-insensitive filter parameters."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_query", {
        "iname": "CONFIG.*",
        "iusername": "ADMIN",
        "igroupname": "WHEEL"
    })
    
    data = json.loads(result["content"][0]["text"])
    query = data["query"]
    
    assert "iname=CONFIG.*" in query
    assert "iusername=ADMIN" in query
    assert "igroupname=WHEEL" in query


@pytest.mark.asyncio
async def test_permission_filters(mock_starfish_client):
    """Test permission filter parameters.""" 
    tools = StarfishTools(mock_starfish_client)
    
    test_cases = [
        {"perm": "644"},        # Exact permissions
        {"perm": "-u=r"},       # At least user read
        {"perm": "/222"},       # Any write permission
    ]
    
    for case in test_cases:
        result = await tools.handle_tool_call("starfish_query", case)
        data = json.loads(result["content"][0]["text"])
        query = data["query"]
        
        for key, value in case.items():
            assert f"{key}={value}" in query


@pytest.mark.asyncio
async def test_query_options_flags(mock_starfish_client):
    """Test query option boolean flags."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_query", {
        "search_all": True,
        "versions": True,
        "children_only": True,
        "file_type": "f"
    })
    
    data = json.loads(result["content"][0]["text"])
    query = data["query"]
    
    assert "search-all" in query
    assert "versions" in query  
    assert "children-only" in query
    assert "type=f" in query


@pytest.mark.asyncio
async def test_list_volumes_tool(mock_starfish_client):
    """Test list volumes tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_list_volumes", {})
    
    # Parse JSON response from new dict format
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "volumes" in data
    assert "total_volumes" in data
    assert isinstance(data["volumes"], list)


@pytest.mark.asyncio
async def test_list_zones_tool(mock_starfish_client):
    """Test list zones tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_list_zones", {})
    
    # Parse JSON response from new dict format
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "zones" in data
    assert "total_zones" in data
    assert isinstance(data["zones"], list)


@pytest.mark.asyncio
async def test_get_tagset_tool(mock_starfish_client):
    """Test get tagset tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_get_tagset", {
        "tagset_name": "Collections"
    })
    
    # Parse JSON response from new dict format
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "name" in data
    assert "tags" in data
    assert isinstance(data["tags"], list)


@pytest.mark.asyncio
async def test_unknown_tool_error(mock_starfish_client):
    """Test handling of unknown tool calls."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("unknown_tool", {})
    
    content = result["content"][0]["text"]
    assert "Unknown tool" in content


@pytest.mark.asyncio
async def test_starfish_error_handling(mock_starfish_client):
    """Test handling of Starfish API errors."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock client to raise StarfishError
    mock_starfish_client.query = AsyncMock(side_effect=StarfishError(
        code="TEST_ERROR",
        message="Test error message"
    ))
    
    result = await tools.handle_tool_call("starfish_query", {
        "name": "test.txt"
    })
    
    content = result["content"][0]["text"]
    assert "TEST_ERROR" in content
    assert "Test error message" in content


@pytest.mark.asyncio 
async def test_generic_error_handling(mock_starfish_client):
    """Test handling of generic errors."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock client to raise generic exception
    mock_starfish_client.query = AsyncMock(side_effect=ValueError("Generic error"))
    
    result = await tools.handle_tool_call("starfish_query", {
        "name": "test.txt"
    })
    
    content = result["content"][0]["text"]
    assert "Tool execution failed" in content
    assert "Generic error" in content


# NEW GUARDRAIL TESTS

@pytest.mark.asyncio
async def test_query_count_guardrail_enforcement(mock_starfish_client):
    """Test that the 5-query limit is enforced."""
    tools = StarfishTools(mock_starfish_client)
    
    # Reset to ensure clean state
    tools.reset_query_count()
    
    # Run 5 queries successfully  
    for i in range(5):
        result = await tools.handle_tool_call("starfish_query", {
            "limit": 1,
            "format_fields": "fn"
        })
        content = result["content"][0]["text"]
        assert "GUARDRAIL VIOLATION" not in content
        assert tools._query_count == i + 1
    
    # 6th query should be blocked
    result = await tools.handle_tool_call("starfish_query", {
        "limit": 1,
        "format_fields": "fn"
    })
    content = result["content"][0]["text"]
    assert "🚨 GUARDRAIL VIOLATION" in content
    assert "Query limit exceeded (6/5 queries)" in content
    assert tools._query_count == 6


@pytest.mark.asyncio
async def test_query_count_reset_functionality(mock_starfish_client):
    """Test the query count reset functionality."""
    tools = StarfishTools(mock_starfish_client)
    
    # Run queries to hit the limit
    for i in range(5):
        await tools.handle_tool_call("starfish_query", {"limit": 1})
    
    assert tools._query_count == 5
    
    # Reset the counter
    result = await tools.handle_tool_call("starfish_reset_query_count", {})
    content = result["content"][0]["text"]
    assert "Query count reset to 0" in content
    assert tools._query_count == 0
    
    # Should be able to query again
    result = await tools.handle_tool_call("starfish_query", {"limit": 1})
    content = result["content"][0]["text"]
    assert "GUARDRAIL VIOLATION" not in content


def test_guardrail_warnings_in_tool_description(mock_starfish_client):
    """Test that guardrail warnings are present in tool descriptions."""
    tools = StarfishTools(mock_starfish_client)
    tool_list = tools.get_tools()
    
    # Find the main query tool
    query_tool = next(tool for tool in tool_list if tool.name == "starfish_query")
    
    # Check for guardrail warnings in description
    description = query_tool.description
    assert "🚨 CRITICAL GUARDRAILS" in description
    assert "NEVER run more than 5 sequential queries" in description
    assert "20-second timeout" in description
    assert "ANTI-PATTERNS TO AVOID" in description


@pytest.mark.asyncio
async def test_new_management_tools(mock_starfish_client):
    """Test the new zone and volume management tools."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock the new client methods
    mock_starfish_client.get_zone = AsyncMock(return_value={
        "id": 1, "name": "test_zone", "paths": [], "managers": [],
        "managing_groups": [], "tagsets": [], "user_params": {}
    })
    mock_starfish_client.get_volume = AsyncMock(return_value={
        "id": 1, "vol": "test_vol", "display_name": "Test Volume", 
        "root": "/test", "type": "local"
    })
    mock_starfish_client.list_tagsets = AsyncMock(return_value=[
        {"name": "test_tagset", "tags": [], "zones": []}
    ])
    
    # Test get_zone
    result = await tools.handle_tool_call("starfish_get_zone", {"zone_id": 1})
    content = result["content"][0]["text"]
    data = json.loads(content)
    assert data["id"] == 1
    assert data["name"] == "test_zone"
    
    # Test get_volume  
    result = await tools.handle_tool_call("starfish_get_volume", {"volume_id": 1})
    content = result["content"][0]["text"]
    data = json.loads(content)
    assert data["id"] == 1
    assert data["name"] == "test_vol"
    
    # Test list_tagsets
    result = await tools.handle_tool_call("starfish_list_tagsets", {"random_string": "test"})
    content = result["content"][0]["text"]
    data = json.loads(content)
    assert "total_tagsets" in data
    assert "tagsets" in data
