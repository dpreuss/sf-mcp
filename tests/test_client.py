"""Tests for Starfish client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from starfish_mcp.client import StarfishClient, TokenManager
from starfish_mcp.models import StarfishError


@pytest.mark.asyncio
async def test_token_manager_basic():
    """Test basic token manager functionality."""
    token_manager = TokenManager("sf-api-v1:test-token", refresh_hours=16)
    
    token = await token_manager.get_token()
    assert token == "sf-api-v1:test-token"


@pytest.mark.asyncio 
async def test_token_manager_refresh_warning():
    """Test token manager refresh warning."""
    token_manager = TokenManager("sf-api-v1:test-token", refresh_hours=16)
    
    # Simulate old token (issued 16 hours ago)
    token_manager.issued_at = datetime.now() - timedelta(hours=16)
    
    with patch('starfish_mcp.client.logger') as mock_logger:
        token = await token_manager.get_token()
        assert token == "sf-api-v1:test-token"
        mock_logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_starfish_client_context_manager(mock_config):
    """Test StarfishClient as context manager."""
    client = StarfishClient(mock_config)
    
    async with client as c:
        assert c is client
        assert client._session is not None
    
    # Session should be closed after context exit
    assert client._session is None


@pytest.mark.asyncio
async def test_starfish_client_query_mock(mock_config, mock_starfish_client):
    """Test query with mock client."""
    # Test the mock client directly
    response = await mock_starfish_client.query("tag=bar")
    
    assert response.total == 2  # Should find 2 entries with tag "bar"
    assert len(response.entries) == 2
    
    # Check that entries have tag "bar"
    for entry in response.entries:
        assert "bar" in entry.all_tags


@pytest.mark.asyncio
async def test_starfish_client_find_file_mock(mock_config, mock_starfish_client):
    """Test finding files by name with mock client."""
    response = await mock_starfish_client.query("fn~foo")
    
    assert response.total == 1
    assert len(response.entries) == 1
    assert response.entries[0].filename == "foo.pdf"


@pytest.mark.asyncio
async def test_starfish_client_list_volumes_mock(mock_config, mock_starfish_client):
    """Test listing volumes with mock client."""
    volumes = await mock_starfish_client.list_volumes()
    
    assert len(volumes) == 2
    assert volumes[0].vol == "storage1"
    assert volumes[0].display_name == "Primary Storage"
    assert volumes[1].vol == "storage2"
    assert volumes[1].display_name == "Archive Storage"


@pytest.mark.asyncio
async def test_starfish_client_list_collections_mock(mock_config, mock_starfish_client):
    """Test listing collections with mock client."""
    collections = await mock_starfish_client.list_collections()
    
    assert len(collections) == 4
    assert "TestData" in collections
    assert "Documents" in collections
    assert "Analytics" in collections
    assert "Configuration" in collections


@pytest.mark.asyncio
async def test_starfish_client_get_tagset_mock(mock_config, mock_starfish_client):
    """Test getting tagset with mock client."""
    tagset_response = await mock_starfish_client.get_tagset("Collections")
    
    assert len(tagset_response.tag_names) == 4
    tag_names = [tag.name for tag in tagset_response.tag_names]
    assert "TestData" in tag_names
    assert "Documents" in tag_names


@pytest.mark.asyncio
async def test_mock_client_request_logging(mock_config, mock_starfish_client):
    """Test that mock client logs requests for debugging."""
    await mock_starfish_client.query("tag=test")
    await mock_starfish_client.list_volumes()
    await mock_starfish_client.list_collections()
    await mock_starfish_client.get_tagset("TestTagset")
    
    # Check request log
    assert len(mock_starfish_client.request_log) == 4
    
    assert mock_starfish_client.request_log[0]["method"] == "query"
    assert mock_starfish_client.request_log[0]["query"] == "tag=test"
    
    assert mock_starfish_client.request_log[1]["method"] == "list_volumes"
    assert mock_starfish_client.request_log[2]["method"] == "list_collections"
    
    assert mock_starfish_client.request_log[3]["method"] == "get_tagset"
    assert mock_starfish_client.request_log[3]["tagset_name"] == "TestTagset"


@pytest.mark.asyncio
async def test_mock_client_directory_search(mock_config, mock_starfish_client):
    """Test directory search with mock client."""
    response = await mock_starfish_client.query("parent_path~/baz")
    
    # Should find files in /baz directory
    assert response.total >= 1
    for entry in response.entries:
        assert "/baz" in entry.parent_path
