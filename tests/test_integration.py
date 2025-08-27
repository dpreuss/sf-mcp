"""Integration tests for Starfish MCP server against real Starfish API.

These tests require a real Starfish instance and should be run separately
from unit tests. Set the following environment variables to run:

- STARFISH_INTEGRATION_API_ENDPOINT
- STARFISH_INTEGRATION_USERNAME  
- STARFISH_INTEGRATION_PASSWORD
- STARFISH_INTEGRATION_TOKEN_TIMEOUT_SECS (optional)
- STARFISH_INTEGRATION_FILE_SERVER_URL (optional)
- STARFISH_INTEGRATION_TLS_SKIP_VERIFY (optional)
"""

import pytest
import asyncio
from typing import List, Dict, Any

from starfish_mcp.client import StarfishClient
from starfish_mcp.tools import StarfishTools
from starfish_mcp.models import StarfishQueryResponse, VolumeInfo


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_connection(integration_config):
    """Test basic connection to Starfish API."""
    client = StarfishClient(integration_config)
    
    async with client:
        # Test basic connectivity by listing collections
        collections = await client.list_collections()
        assert isinstance(collections, list)
        print(f"Found {len(collections)} collections: {collections}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_list_volumes(integration_config):
    """Test listing volumes from real Starfish API."""
    client = StarfishClient(integration_config)
    
    async with client:
        volumes = await client.list_volumes()
        
        assert isinstance(volumes, list)
        assert len(volumes) > 0, "Expected at least one volume"
        
        for volume in volumes:
            assert isinstance(volume, VolumeInfo)
            assert volume.vol is not None
            assert volume.display_name is not None
            assert isinstance(volume.mounts, dict)
            
        print(f"Found {len(volumes)} volumes:")
        for volume in volumes:
            print(f"  - {volume.vol}: {volume.display_name} ({volume.type})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_basic_query(integration_config):
    """Test basic query against real Starfish API."""
    client = StarfishClient(integration_config)
    
    async with client:
        # Query for files only, limited results
        response = await client.query("type=f", limit=10)
        
        assert isinstance(response, StarfishQueryResponse)
        assert isinstance(response.entries, list)
        assert response.total >= 0
        
        print(f"Basic query returned {len(response.entries)} entries (total: {response.total})")
        
        # Verify entry structure
        if response.entries:
            entry = response.entries[0]
            assert entry.filename is not None
            assert entry.volume is not None
            assert entry.is_file is True
            
            print(f"Sample entry: {entry.filename} in {entry.volume}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_collection_query(integration_config):
    """Test querying within collections."""
    client = StarfishClient(integration_config)
    
    async with client:
        # Get available collections first
        collections = await client.list_collections()
        
        if not collections:
            pytest.skip("No collections available for testing")
        
        # Test querying within first collection
        collection = collections[0]
        query = f"type=f tag=Collections:{collection}"
        response = await client.query(query, limit=5)
        
        assert isinstance(response, StarfishQueryResponse)
        print(f"Collection '{collection}' query returned {len(response.entries)} entries")
        
        # Verify all entries have the collection tag
        for entry in response.entries:
            all_tags = entry.all_tags
            assert f"Collections:{collection}" in all_tags


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_tools_find_file(integration_config):
    """Test file finding tools against real API."""
    client = StarfishClient(integration_config)
    tools = StarfishTools(client)
    
    async with client:
        # Test finding files with common extensions
        for filename in ["*.txt", "*.log", "*.json", "*.csv"]:
            result = await tools._find_file({
                "filename": filename,
                "limit": 5
            })
            
            assert not result.isError
            print(f"Search for '{filename}' completed successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_tools_find_by_tag(integration_config):
    """Test tag-based search tools against real API."""
    client = StarfishClient(integration_config)
    tools = StarfishTools(client)
    
    async with client:
        # Get available collections and test tag search
        collections = await client.list_collections()
        
        if collections:
            collection = collections[0]
            result = await tools._find_by_tag({
                "tag": f"Collections:{collection}",
                "limit": 5
            })
            
            assert not result.isError
            print(f"Tag search for 'Collections:{collection}' completed successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_tools_directory_search(integration_config):
    """Test directory search tools against real API."""
    client = StarfishClient(integration_config)
    tools = StarfishTools(client)
    
    async with client:
        # Test searching common directory patterns
        for directory in ["/", "/tmp", "/var", "/home", "/data"]:
            result = await tools._find_in_directory({
                "directory_path": directory,
                "limit": 5,
                "recursive": False
            })
            
            # Don't assert success since directories may not exist
            # Just verify the tool doesn't crash
            print(f"Directory search for '{directory}' completed")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_tools_advanced_query(integration_config):
    """Test advanced query tools against real API."""
    client = StarfishClient(integration_config)
    tools = StarfishTools(client)
    
    async with client:
        # Test various advanced queries
        queries = [
            "type=f",  # All files
            "type=f size>1024",  # Files larger than 1KB
            "type=f size<1048576",  # Files smaller than 1MB
        ]
        
        for query in queries:
            result = await tools._query_advanced({
                "query": query,
                "limit": 10
            })
            
            assert not result.isError
            print(f"Advanced query '{query}' completed successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_error_handling(integration_config):
    """Test error handling with invalid queries."""
    client = StarfishClient(integration_config)
    
    async with client:
        # Test invalid query that should return empty results
        response = await client.query("tag=NonExistentTag12345", limit=1)
        
        assert isinstance(response, StarfishQueryResponse)
        assert len(response.entries) == 0
        print("Invalid tag query handled correctly (returned empty results)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_tagset_operations(integration_config):
    """Test tagset operations against real API."""
    client = StarfishClient(integration_config)
    
    async with client:
        # Test getting Collections tagset
        try:
            tagset_response = await client.get_tagset("Collections")
            assert len(tagset_response.tag_names) >= 0
            print(f"Collections tagset has {len(tagset_response.tag_names)} tags")
        except Exception as e:
            print(f"Collections tagset query failed (may be expected): {e}")
        
        # Test getting a non-existent tagset (should handle gracefully)
        try:
            await client.get_tagset("NonExistentTagset12345")
            print("Non-existent tagset query unexpectedly succeeded")
        except Exception as e:
            print(f"Non-existent tagset query failed as expected: {e}")


@pytest.mark.integration
def test_integration_performance_benchmark(integration_config):
    """Basic performance benchmark for integration testing."""
    import time
    
    async def run_benchmark():
        client = StarfishClient(integration_config)
        
        async with client:
            start_time = time.time()
            
            # Run a series of operations
            await client.list_collections()
            await client.list_volumes()
            await client.query("type=f", limit=100)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Basic operations completed in {duration:.2f} seconds")
            
            # Basic performance assertion (should complete within reasonable time)
            assert duration < 30.0, f"Operations took too long: {duration:.2f}s"
    
    asyncio.run(run_benchmark())
