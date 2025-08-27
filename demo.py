#!/usr/bin/env python3
"""Demo script to showcase Starfish MCP server functionality with mock data."""

import asyncio
import json
from typing import Dict, Any, List

# Mock data (simplified version of test fixtures)
def get_sample_entries() -> List[Dict[str, Any]]:
    """Get sample Starfish entries for demo."""
    return [
        {
            "_id": 12345,
            "fn": "foo.pdf",
            "parent_path": "/documents",
            "full_path": "/documents/foo.pdf",
            "type": 32768,
            "size": 2048576,
            "volume": "storage1",
            "mt": 1640995200,
            "tags_explicit": "document:pdf,important",
            "tags_inherited": "Collections:Documents",
        },
        {
            "_id": 12346,
            "fn": "data.csv",
            "parent_path": "/baz",
            "full_path": "/baz/data.csv",
            "type": 32768,
            "size": 512000,
            "volume": "storage1",
            "mt": 1640995300,
            "tags_explicit": "bar,data:csv",
            "tags_inherited": "Collections:Analytics",
        },
        {
            "_id": 12347,
            "fn": "config.json",
            "parent_path": "/baz/config",
            "full_path": "/baz/config/config.json",
            "type": 32768,
            "size": 4096,
            "volume": "storage1",
            "mt": 1640995400,
            "tags_explicit": "config,bar",
            "tags_inherited": "Collections:Configuration",
        }
    ]

def demo_basic_models():
    """Demonstrate basic data model functionality."""
    print("🔹 Demo: Starfish Data Models")
    print("=" * 50)
    
    from starfish_mcp.models import StarfishEntry, StarfishQueryResponse
    
    sample_data = get_sample_entries()[0]  # First entry
    entry = StarfishEntry(**sample_data)
    
    print(f"📄 File: {entry.filename}")
    print(f"📁 Path: {entry.full_path}")
    print(f"📦 Volume: {entry.volume}")
    print(f"💾 Size: {entry.size:,} bytes")
    print(f"🏷️  Explicit Tags: {entry.tags_explicit}")
    print(f"🏷️  Inherited Tags: {entry.tags_inherited}")
    print(f"🏷️  All Tags: {entry.all_tags}")
    print(f"📅 Modified: {entry.modify_time}")
    print(f"📋 Is File: {entry.is_file}")
    print()

def demo_config():
    """Demonstrate configuration functionality."""
    print("🔹 Demo: Configuration Management")
    print("=" * 50)
    
    from starfish_mcp.config import StarfishConfig
    
    # Create a sample config
    config = StarfishConfig(
        api_endpoint="https://sf-redashdev.sfish.dev/api/",
        username="demo",
        password="demo",
        token_timeout_secs=57600,
        file_server_url="https://files.starfish.com",
        cache_ttl_hours=2,
        log_level="debug"
    )
    
    print(f"🌐 API Endpoint: {config.api_endpoint}")
    print(f"👤 Username: {config.username}")
    print(f"🔑 Password: {'*' * len(config.password)}")
    print(f"⏰ Token Timeout: {config.token_timeout_secs / 3600:.1f} hours")
    print(f"📁 File Server: {config.file_server_url}")
    print(f"💾 Cache TTL: {config.cache_ttl_hours} hours")
    print(f"📊 Log Level: {config.log_level}")
    print()

def demo_mock_queries():
    """Demonstrate mock query functionality."""
    print("🔹 Demo: Mock Query Operations")
    print("=" * 50)
    
    # Simple mock query simulation
    entries = get_sample_entries()
    
    # Simulate finding files by name
    print("🔍 Search: Find files named 'foo'")
    foo_files = [e for e in entries if "foo" in e["fn"].lower()]
    print(f"   Found {len(foo_files)} file(s):")
    for f in foo_files:
        print(f"   - {f['fn']} ({f['size']:,} bytes)")
    print()
    
    # Simulate finding files by tag
    print("🔍 Search: Find files with tag 'bar'")
    bar_files = [e for e in entries if "bar" in e.get("tags_explicit", "")]
    print(f"   Found {len(bar_files)} file(s):")
    for f in bar_files:
        print(f"   - {f['fn']} in {f['parent_path']}")
    print()
    
    # Simulate finding files in directory
    print("🔍 Search: Find files in '/baz' directory")
    baz_files = [e for e in entries if "/baz" in e.get("parent_path", "")]
    print(f"   Found {len(baz_files)} file(s):")
    for f in baz_files:
        print(f"   - {f['fn']} ({f['size']:,} bytes)")
    print()

def demo_authentication_flow():
    """Demonstrate authentication flow."""
    print("🔹 Demo: Authentication Flow")
    print("=" * 50)
    
    print("🔐 Starfish Authentication Process:")
    print("   1. 📝 User provides username/password in .env file")
    print("   2. 🌐 MCP server calls POST /auth/ endpoint with credentials")
    print("   3. 🎫 Starfish returns bearer token (format: sf-api-v1:token_id:token_secret)")
    print("   4. ⏰ Token is valid for 16 hours (configurable)")
    print("   5. 🔄 MCP server automatically refreshes token 1 hour before expiry")
    print("   6. 🛡️  All API calls use 'Authorization: Bearer <token>' header")
    print()
    
    print("📋 Authentication Request Example:")
    print("   POST https://sf-redashdev.sfish.dev/api/auth/")
    print("   Content-Type: application/json")
    print("   {")
    print('     "username": "demo",')
    print('     "password": "demo",')
    print('     "token_timeout_secs": 57600,')
    print('     "token_description": "Starfish MCP Server",')
    print('     "auto_generated": true')
    print("   }")
    print()
    
    print("✅ Benefits of username/password authentication:")
    print("   • 🔄 Automatic token refresh (no manual token management)")
    print("   • 🛡️  Secure storage (password in .env, not long-lived token)")
    print("   • ⏰ Configurable token timeout")
    print("   • 📝 Token descriptions for auditing")
    print()

def demo_tools_schema():
    """Demonstrate MCP tools schema."""
    print("🔹 Demo: MCP Tools Schema")
    print("=" * 50)
    
    # Mock the tool definitions (simplified)
    tools = [
        {
            "name": "starfish_find_file",
            "description": "Find files by name pattern",
            "parameters": ["filename", "collection?", "limit?"]
        },
        {
            "name": "starfish_find_by_tag", 
            "description": "Find files with specific tags",
            "parameters": ["tag", "collection?", "limit?"]
        },
        {
            "name": "starfish_find_in_directory",
            "description": "Find files in directory path",
            "parameters": ["directory_path", "recursive?", "limit?"]
        },
        {
            "name": "starfish_query_advanced",
            "description": "Execute advanced Starfish queries",
            "parameters": ["query", "format_fields?", "limit?", "sort_by?"]
        },
        {
            "name": "starfish_list_volumes",
            "description": "List all available volumes",
            "parameters": []
        },
        {
            "name": "starfish_list_collections",
            "description": "List available collections",
            "parameters": ["force_refresh?"]
        },
        {
            "name": "starfish_list_zones",
            "description": "List all available zones with detailed information",
            "parameters": []
        }
    ]
    
    print("🛠️  Available MCP Tools:")
    for tool in tools:
        print(f"   📋 {tool['name']}")
        print(f"      {tool['description']}")
        if tool['parameters']:
            params = ", ".join(tool['parameters'])
            print(f"      Parameters: {params}")
        print()

def main():
    """Run the complete demo."""
    print("🌟 Starfish MCP Server Demo")
    print("🌟 Mock Data & Functionality Showcase")
    print("=" * 60)
    print()
    
    try:
        demo_basic_models()
        demo_config()
        demo_authentication_flow()
        demo_mock_queries()
        demo_tools_schema()
        
        print("✅ Demo completed successfully!")
        print("\n💡 Next Steps:")
        print("   1. Copy env.example to .env: cp env.example .env")
        print("   2. Update .env with your Starfish credentials (demo/demo works!)")
        print("   3. Install dependencies: pip install -e .")
        print("   4. Run the MCP server: python -m starfish_mcp.server")
        print("   5. Run integration tests: make test-integration")
        print("\n🌟 Ready to use with demo/demo credentials on sf-redashdev.sfish.dev!")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Install dependencies first:")
        print("   pip install -e .")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
