"""Tests for Starfish client functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from starfish_mcp.client import StarfishClient, TokenManager
from starfish_mcp.models import StarfishError


@pytest.mark.asyncio
async def test_token_manager_creation(mock_config):
    """Test creating token manager."""
    token_manager = TokenManager(mock_config)
    
    # Just test the object creation for now
    assert token_manager.config == mock_config


# Token manager and context manager functionality tested through integration


@pytest.mark.asyncio
async def test_starfish_client_creation(mock_config):
    """Test basic StarfishClient creation."""
    client = StarfishClient(mock_config)
    assert client.config == mock_config
    assert client.token_manager is not None


@pytest.mark.asyncio
async def test_client_timeout_handling(mock_config):
    """Test that client properly handles timeout in requests."""
    client = StarfishClient(mock_config)
    
    # Mock aiohttp to raise TimeoutError
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.side_effect = asyncio.TimeoutError()
        
        # Mock token manager
        with patch.object(client, 'token_manager') as mock_token_manager:
            mock_token_manager.get_token = AsyncMock(return_value="test-token")
            
            with pytest.raises(StarfishError) as exc_info:
                await client._request("GET", "/test", timeout_seconds=5)
            
            assert exc_info.value.code == "REQUEST_TIMEOUT"
            assert "timed out after 5 seconds" in exc_info.value.message


@pytest.mark.asyncio
async def test_client_timeout_custom_value(mock_config):
    """Test client timeout with custom timeout value."""
    client = StarfishClient(mock_config)
    
    # Mock aiohttp to raise TimeoutError
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.side_effect = asyncio.TimeoutError()
        
        # Mock token manager
        with patch.object(client, 'token_manager') as mock_token_manager:
            mock_token_manager.get_token = AsyncMock(return_value="test-token")
            
            with pytest.raises(StarfishError) as exc_info:
                await client._request("GET", "/test", timeout_seconds=10)
            
            assert exc_info.value.code == "REQUEST_TIMEOUT"
            assert "timed out after 10 seconds" in exc_info.value.message


@pytest.mark.asyncio
async def test_timeout_implementation_correctness(mock_config):
    """Test that the timeout implementation doesn't break normal requests."""
    import aiohttp
    from unittest.mock import AsyncMock
    
    client = StarfishClient(mock_config)
    
    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content_type = "application/json"
    mock_response.json = AsyncMock(return_value={"test": "data"})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    # Properly mock the actual async function
    async def mock_request_func(*args, **kwargs):
        return mock_response
    
    with patch('aiohttp.ClientSession.request', side_effect=mock_request_func):
        with patch.object(client, 'token_manager') as mock_token_manager:
            mock_token_manager.get_token = AsyncMock(return_value="test-token")
            
            # This should work without any timeout issues
            result = await client._request("GET", "/test")
            
            assert result == {"test": "data"}


@pytest.mark.asyncio
async def test_timeout_with_slow_response(mock_config):
    """Test timeout with actual slow response simulation."""
    import asyncio
    
    client = StarfishClient(mock_config)
    
    async def slow_request(*args, **kwargs):
        await asyncio.sleep(2)  # Simulate slow response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json = AsyncMock(return_value={"test": "data"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        return mock_response
    
    with patch('aiohttp.ClientSession.request', side_effect=slow_request):
        with patch.object(client, 'token_manager') as mock_token_manager:
            mock_token_manager.get_token = AsyncMock(return_value="test-token")
            
            # Should timeout after 1 second
            with pytest.raises(StarfishError) as exc_info:
                await client._request("GET", "/test", timeout_seconds=1)
            
            assert exc_info.value.code == "REQUEST_TIMEOUT"
            assert "timed out after 1 seconds" in exc_info.value.message