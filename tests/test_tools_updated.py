"""Tests for updated MCP tools with guardrails."""

import pytest
import json
from unittest.mock import AsyncMock, patch

from starfish_mcp.tools import StarfishTools
from starfish_mcp.models import StarfishError


@pytest.mark.asyncio
async def test_starfish_query_tool(mock_starfish_client):
    """Test the main starfish_query tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_query", {
        "file_type": "f",
        "limit": 10,
        "format_fields": "fn size mtime"
    })
    
    # Parse JSON response
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "entries" in data
    assert "total_found" in data
    assert data["total_found"] >= 0
    assert len(data["entries"]) <= 10


@pytest.mark.asyncio 
async def test_starfish_query_with_rec_aggrs(mock_starfish_client):
    """Test directory analysis with recursive aggregates."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_query", {
        "file_type": "d",
        "depth": 1, 
        "format_fields": "fn rec_aggrs",
        "sort_by": "-rec_aggrs.size"
    })
    
    content = result["content"][0]["text"] 
    data = json.loads(content)
    
    assert "entries" in data
    # Check that recursive aggregates are included
    if data["entries"]:
        entry = data["entries"][0]
        if "recursive_aggregates" in entry:
            assert "size" in entry["recursive_aggregates"]
            assert "files" in entry["recursive_aggregates"]


@pytest.mark.asyncio
async def test_query_count_guardrail(mock_starfish_client):
    """Test that query count guardrail is enforced."""
    tools = StarfishTools(mock_starfish_client)
    
    # Run 5 queries successfully
    for i in range(5):
        result = await tools.handle_tool_call("starfish_query", {
            "limit": 1,
            "format_fields": "fn"
        })
        content = result["content"][0]["text"]
        assert "GUARDRAIL VIOLATION" not in content
    
    # 6th query should be blocked
    result = await tools.handle_tool_call("starfish_query", {
        "limit": 1,
        "format_fields": "fn"
    })
    content = result["content"][0]["text"]
    assert "GUARDRAIL VIOLATION" in content
    assert "Query limit exceeded" in content


@pytest.mark.asyncio
async def test_reset_query_count(mock_starfish_client):
    """Test resetting query count."""
    tools = StarfishTools(mock_starfish_client)
    
    # Run 5 queries to hit limit
    for i in range(5):
        await tools.handle_tool_call("starfish_query", {"limit": 1})
    
    # Reset counter
    result = await tools.handle_tool_call("starfish_reset_query_count", {})
    content = result["content"][0]["text"]
    assert "Query count reset" in content
    
    # Should be able to query again
    result = await tools.handle_tool_call("starfish_query", {"limit": 1})
    content = result["content"][0]["text"]
    assert "GUARDRAIL VIOLATION" not in content


@pytest.mark.asyncio
async def test_starfish_list_volumes(mock_starfish_client):
    """Test listing volumes."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_list_volumes", {})
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "total_volumes" in data
    assert "volumes" in data
    assert isinstance(data["volumes"], list)


@pytest.mark.asyncio
async def test_starfish_get_volume(mock_starfish_client):
    """Test getting specific volume details."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock the get_volume method
    mock_volume_data = {
        "id": 1,
        "vol": "test_volume",
        "display_name": "Test Volume",
        "root": "/test",
        "type": "local",
        "total_capacity": 1000000,
        "free_space": 500000
    }
    mock_starfish_client.get_volume = AsyncMock(return_value=mock_volume_data)
    
    result = await tools.handle_tool_call("starfish_get_volume", {"volume_id": 1})
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert data["id"] == 1
    assert data["name"] == "test_volume"
    assert data["display_name"] == "Test Volume"


@pytest.mark.asyncio
async def test_starfish_list_zones(mock_starfish_client):
    """Test listing zones."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_list_zones", {})
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "total_zones" in data
    assert "zones" in data
    assert isinstance(data["zones"], list)


@pytest.mark.asyncio
async def test_starfish_get_zone(mock_starfish_client):
    """Test getting specific zone details."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock the get_zone method
    mock_zone_data = {
        "id": 2,
        "name": "test_zone",
        "paths": ["/test/path"],
        "managers": [],
        "managing_groups": [],
        "tagsets": [],
        "user_params": {},
        "aggregates": {
            "size": 1000000,
            "files": 100,
            "dirs": 10
        }
    }
    mock_starfish_client.get_zone = AsyncMock(return_value=mock_zone_data)
    
    result = await tools.handle_tool_call("starfish_get_zone", {"zone_id": 2})
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert data["id"] == 2
    assert data["name"] == "test_zone"
    assert data["paths"] == ["/test/path"]


@pytest.mark.asyncio
async def test_starfish_list_tagsets(mock_starfish_client):
    """Test listing tagsets."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock the list_tagsets method
    mock_tagsets_data = [
        {
            "name": "test_tagset",
            "zone_ids": [1],
            "inheritable": True,
            "pinnable": False,
            "action": "CLASSIFICATION",
            "tags": [{"id": 1, "name": "test_tag"}],
            "zones": []
        }
    ]
    mock_starfish_client.list_tagsets = AsyncMock(return_value=mock_tagsets_data)
    
    result = await tools.handle_tool_call("starfish_list_tagsets", {"random_string": "test"})
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "total_tagsets" in data
    assert "tagsets" in data
    assert isinstance(data["tagsets"], list)
    if data["tagsets"]:
        tagset = data["tagsets"][0]
        assert "name" in tagset
        assert "tag_count" in tagset


@pytest.mark.asyncio
async def test_starfish_get_tagset(mock_starfish_client):
    """Test getting specific tagset details.""" 
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_get_tagset", {"tagset_name": "test"})
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert "name" in data
    assert "tags" in data
    assert "zones" in data


@pytest.mark.asyncio
async def test_timeout_handling(mock_starfish_client):
    """Test that timeout errors are handled properly."""
    import asyncio
    
    # Mock timeout error
    mock_starfish_client.async_query = AsyncMock(side_effect=asyncio.TimeoutError())
    
    tools = StarfishTools(mock_starfish_client)
    
    with pytest.raises(StarfishError) as exc_info:
        await tools.handle_tool_call("starfish_query", {"limit": 1})
    
    # The StarfishError should be caught and re-raised by the tool handler
    # But since we're mocking at the client level, we expect the timeout to propagate


@pytest.mark.asyncio  
async def test_tool_error_handling(mock_starfish_client):
    """Test that tool errors are handled gracefully."""
    # Mock an API error
    mock_starfish_client.async_query = AsyncMock(side_effect=StarfishError(
        code="TEST_ERROR",
        message="Test error message"
    ))
    
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("starfish_query", {"limit": 1})
    
    content = result["content"][0]["text"]
    assert "Starfish API error" in content


@pytest.mark.asyncio
async def test_unknown_tool_handling(mock_starfish_client):
    """Test handling of unknown tool names."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("unknown_tool", {})
    
    content = result["content"][0]["text"]
    assert "Unknown tool" in content


@pytest.mark.asyncio
async def test_tag_counting_pattern(mock_starfish_client):
    """Test the recommended pattern for counting files by tag."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock response with total_found
    mock_response = [{"total_found": 42, "entries": []}]
    mock_starfish_client.async_query = AsyncMock(return_value=mock_response)
    
    result = await tools.handle_tool_call("starfish_query", {
        "tag": "production",
        "limit": 0,  # Only want count
        "format_fields": "fn"
    })
    
    content = result["content"][0]["text"]
    data = json.loads(content)
    
    assert data["total_found"] == 42
    assert len(data["entries"]) == 0  # No actual entries with limit=0


def test_tools_list_includes_all_tools(mock_starfish_client):
    """Test that all expected tools are registered."""
    tools = StarfishTools(mock_starfish_client)
    tool_list = tools.get_tools()
    
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
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"


def test_query_tool_has_guardrail_warnings(mock_starfish_client):
    """Test that the main query tool description includes guardrail warnings."""
    tools = StarfishTools(mock_starfish_client)
    tool_list = tools.get_tools()
    
    query_tool = next(tool for tool in tool_list if tool.name == "starfish_query")
    
    assert "🚨 CRITICAL GUARDRAILS" in query_tool.description
    assert "NEVER run more than 5 sequential queries" in query_tool.description
    assert "20-second timeout" in query_tool.description
