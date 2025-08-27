"""Tests for MCP tools."""

import pytest
import json
from unittest.mock import AsyncMock

from starfish_mcp.tools import StarfishTools
from starfish_mcp.models import StarfishError


@pytest.mark.asyncio
async def test_find_file_tool(mock_starfish_client):
    """Test find file tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._find_file({
        "filename": "foo",
        "limit": 10
    })
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    assert "files" in data
    assert data["total_found"] >= 0
    assert len(data["files"]) <= 10
    
    # Should find the foo.pdf file
    found_foo = any(f["filename"] == "foo.pdf" for f in data["files"])
    assert found_foo


@pytest.mark.asyncio
async def test_find_by_tag_tool(mock_starfish_client):
    """Test find by tag tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._find_by_tag({
        "tag": "bar",
        "limit": 10
    })
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    assert "files" in data
    assert data["total_found"] >= 0
    
    # Should find files with tag "bar"
    for file_info in data["files"]:
        all_tags = file_info["tags_explicit"] + file_info["tags_inherited"]
        assert "bar" in all_tags


@pytest.mark.asyncio
async def test_find_in_directory_tool(mock_starfish_client):
    """Test find in directory tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._find_in_directory({
        "directory_path": "/baz",
        "recursive": True,
        "limit": 10
    })
    
    assert not result.isError
    
    # Parse JSON response  
    content = result.content[0].text
    data = json.loads(content)
    
    assert "files" in data
    assert data["directory_path"] == "/baz"
    assert data["recursive"] is True
    
    # Should find files in /baz directory
    for file_info in data["files"]:
        assert "/baz" in file_info["parent_path"]


@pytest.mark.asyncio
async def test_query_advanced_tool(mock_starfish_client):
    """Test advanced query tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._query_advanced({
        "query": "type=f tag=bar",
        "limit": 5
    })
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    assert "entries" in data
    assert data["query"] == "type=f tag=bar"
    assert len(data["entries"]) <= 5


@pytest.mark.asyncio
async def test_list_volumes_tool(mock_starfish_client):
    """Test list volumes tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._list_volumes({})
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    assert "volumes" in data
    assert data["total_volumes"] >= 0
    
    # Check volume structure
    if data["volumes"]:
        volume = data["volumes"][0]
        assert "id" in volume
        assert "volume_name" in volume
        assert "display_name" in volume
        assert "mounts" in volume


@pytest.mark.asyncio
async def test_list_collections_tool(mock_starfish_client):
    """Test list collections tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._list_collections({})
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    assert "collections" in data
    assert data["total_collections"] >= 0
    assert isinstance(data["collections"], list)


@pytest.mark.asyncio
async def test_get_tagset_tool(mock_starfish_client):
    """Test get tagset tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._get_tagset({
        "tagset_name": "Collections",
        "limit": 100
    })
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    assert "tags" in data
    assert data["tagset_name"] == "Collections"
    assert data["total_tags"] >= 0
    assert isinstance(data["tags"], list)


@pytest.mark.asyncio
async def test_handle_unknown_tool(mock_starfish_client):
    """Test handling of unknown tool."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools.handle_tool_call("unknown_tool", {})
    
    assert result.isError
    assert "Unknown tool" in result.content[0].text


@pytest.mark.asyncio
async def test_handle_starfish_error(mock_starfish_client):
    """Test handling of Starfish API errors."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock client to raise StarfishError
    mock_starfish_client.query = AsyncMock(side_effect=StarfishError(
        code="TEST_ERROR",
        message="Test error message"
    ))
    
    result = await tools._find_file({
        "filename": "test",
        "limit": 10
    })
    
    assert result.isError
    assert "TEST_ERROR" in result.content[0].text
    assert "Test error message" in result.content[0].text


@pytest.mark.asyncio
async def test_handle_generic_error(mock_starfish_client):
    """Test handling of generic errors."""
    tools = StarfishTools(mock_starfish_client)
    
    # Mock client to raise generic exception
    mock_starfish_client.query = AsyncMock(side_effect=ValueError("Generic error"))
    
    result = await tools._find_file({
        "filename": "test",
        "limit": 10
    })
    
    assert result.isError
    assert "Tool execution failed" in result.content[0].text
    assert "Generic error" in result.content[0].text


@pytest.mark.asyncio
async def test_tool_with_collection_filter(mock_starfish_client):
    """Test tools with collection filtering."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._find_file({
        "filename": "test",
        "collection": "TestData",
        "limit": 10
    })
    
    assert not result.isError
    
    # Verify that the query included the collection filter
    # Check the last request made to mock client
    last_request = mock_starfish_client.request_log[-1]
    assert "Collections:TestData" in last_request["query"]


@pytest.mark.asyncio
async def test_wildcard_filename_search(mock_starfish_client):
    """Test wildcard filename search."""
    tools = StarfishTools(mock_starfish_client)
    
    result = await tools._find_file({
        "filename": "*.pdf",
        "limit": 10
    })
    
    assert not result.isError
    
    # Parse JSON response
    content = result.content[0].text
    data = json.loads(content)
    
    # Should find PDF files
    pdf_files = [f for f in data["files"] if f["filename"].endswith(".pdf")]
    assert len(pdf_files) > 0


def test_get_tools_list(mock_starfish_client):
    """Test getting list of available tools."""
    tools = StarfishTools(mock_starfish_client)
    
    tool_list = tools.get_tools()
    
    assert len(tool_list) > 0
    
    # Check that expected tools are present
    tool_names = [tool.name for tool in tool_list]
    expected_tools = [
        "starfish_find_file",
        "starfish_find_by_tag", 
        "starfish_find_in_directory",
        "starfish_query_advanced",
        "starfish_list_volumes",
        "starfish_list_collections",
        "starfish_get_tagset"
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
