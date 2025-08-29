# Starfish MCP Server for Cursor IDE

An MCP (Model Context Protocol) server for Starfish Storage integration. This server provides tools for querying files, managing volumes, zones, and tagsets through the Starfish API with built-in performance guardrails.

## Features

- **🔍 Advanced File Search**: Comprehensive search with 19+ filter parameters (name, size, timestamps, permissions, tags)
- **📁 Volume & Zone Management**: List and inspect Starfish volumes and zones with detailed metadata
- **🏷️ Tagset Support**: Full tagset management with tag counts and zone associations
- **⚡ Optimized Queries**: Built-in query optimization with recursive aggregates for directory analysis
- **🚨 Performance Guardrails**: 20-second timeouts and 5-query limits to prevent inefficient usage
- **🔐 Authentication**: Username/password authentication with automatic token refresh
- **📊 Rich Metadata**: Returns detailed file metadata including zones, tags, ownership, permissions
- **🛡️ Error Handling**: Comprehensive error handling and logging

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd starfish-mcp

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file based on the provided example:

```bash
cp env.example .env
```

Edit `.env` with your Starfish configuration:

```env
# Required
STARFISH_API_ENDPOINT=https://sf-redashdev.sfish.dev/api
STARFISH_USERNAME=demo
STARFISH_PASSWORD=demo

# Optional
STARFISH_TOKEN_TIMEOUT_SECS=57600
STARFISH_FILE_SERVER_URL=https://your-starfish-fileserver.com
CACHE_TTL_HOURS=1
LOG_LEVEL=INFO
```

## MCP Configuration for Cursor

Add this MCP server to your Cursor settings:

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP"
3. Add this configuration to your MCP servers:

```json
{
  "mcpServers": {
    "starfish": {
      "command": "python",
      "args": ["-m", "starfish_mcp.server"],
      "cwd": "/Users/Don/src/sf-mcp",
      "env": {
        "STARFISH_API_ENDPOINT": "https://sf-redashdev.sfish.dev/api",
        "STARFISH_USERNAME": "demo", 
        "STARFISH_PASSWORD": "demo"
      }
    }
  }
}
```

## Available Tools

### 🔍 Core Search Tool

#### `starfish_query` - Comprehensive File Search
The main tool with 19 filter parameters and built-in guardrails.

**Key Features:**
- 🚨 **Guardrails**: 20-second timeout, 5-query limit per session
- ⚡ **Optimized**: Use `rec_aggrs` for directory analysis, `total_found` for counts
- 🎯 **Efficient**: Broad queries preferred over multiple narrow ones

**Example Usage:**
```json
{
  "file_type": "f",
  "name": "*.pdf", 
  "size": ">10MB",
  "format_fields": "fn size mtime tags zones",
  "sort_by": "-size",
  "limit": 20
}
```

**Directory Tree Analysis:**
```json
{
  "volumes_and_paths": ["prod:"],
  "file_type": "d",
  "depth": 1,
  "format_fields": "fn rec_aggrs",
  "sort_by": "-rec_aggrs.size"
}
```

### 📁 Management Tools

#### `starfish_list_volumes` - Volume Discovery
List all Starfish storage volumes with capacity and mount information.

#### `starfish_get_volume` - Volume Details
Get detailed information about a specific volume by ID.
```json
{"volume_id": 1}
```

#### `starfish_list_zones` - Zone Discovery  
List all storage zones with paths, managers, and aggregated statistics.

#### `starfish_get_zone` - Zone Details
Get detailed information about a specific zone by ID.
```json
{"zone_id": 2}
```

### 🏷️ Tagset Tools

#### `starfish_list_tagsets` - Tagset Overview
List all tagsets with tag counts, zone associations, and sample tags.

#### `starfish_get_tagset` - Tagset Details
Get complete tagset information including all tags.
```json
{"tagset_name": "gene-seq-c"}
```

#### `starfish_list_tags` - Legacy Tag List
Legacy tool - use `starfish_list_tagsets` for better information.

### 🛠️ Utility Tools

#### `starfish_reset_query_count` - Reset Guardrails
Reset the 5-query limit when starting a new task.

## 🚨 Performance Guardrails

### Critical Limits
- **20-second timeout** on all API calls
- **5-query maximum** per session to prevent inefficient patterns
- **Automatic enforcement** with clear error messages

### Query Best Practices

✅ **DO:**
```python
# Single broad query
starfish_query(volumes_and_paths=[], format_fields="fn rec_aggrs")

# Use total_found for counts
starfish_query(tag="production", limit=0, format_fields="fn")  # Read total_found

# Use recursive aggregates for directory analysis
starfish_query(file_type="d", depth=1, format_fields="fn rec_aggrs")
```

❌ **DON'T:**
```python
# Multiple volume queries (inefficient!)
for volume in volumes:
    starfish_query(volumes_and_paths=[f"{volume}:"])

# Directory crawling (inefficient!)
for directory in directories:
    starfish_query(volumes_and_paths=[f"volume:{directory}"])
```

## Common Usage Patterns

### Find Largest Files
```json
{
  "file_type": "f",
  "limit": 20,
  "format_fields": "parent_path fn size mtime",
  "sort_by": "-size"
}
```

### Directory Tree Sizes
```json
{
  "volumes_and_paths": ["volume:"],
  "file_type": "d", 
  "depth": 1,
  "format_fields": "fn rec_aggrs",
  "sort_by": "-rec_aggrs.size"
}
```

### Count Files by Tag
```json
{
  "tag": "production",
  "limit": 0,
  "format_fields": "fn"
}
```
*Use `total_found` from response for the count*

## Development

### Testing

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/test_tools_modular.py -v      # Tool tests
pytest tests/test_client.py -v             # Client tests
pytest tests/test_integration.py -v        # Integration tests
```

### Local Development

```bash
# Start MCP server locally
make run

# Test with mock data
python demo.py
```

### Code Quality

```bash
# Format code
black starfish_mcp/ tests/

# Lint code  
ruff check starfish_mcp/ tests/

# Type checking
mypy starfish_mcp/
```

## Architecture

```
starfish_mcp/
├── server.py          # MCP server with message handling
├── client.py          # Async HTTP client with auth & caching  
├── models.py          # Pydantic models for API data
├── config.py          # Configuration management
├── prompt.py          # Query optimization guidance
└── tools/
    ├── __init__.py         # Tool registration and handlers
    ├── starfish_query.py   # Main search implementation
    ├── management.py       # Volume/zone/tagset tools
    ├── query_builder.py    # Query parameter processing
    └── schema.py          # Tool schema definitions
```

## API Coverage

This MCP server supports the full Starfish API:

- **Query API**: `/query/` with all 19 filter parameters
- **Volumes API**: `/volume/` for discovery and `/volume/{id}/` for details
- **Zones API**: `/zone/` for listing and `/zone/{id}/` for details  
- **Tagsets API**: `/tagset/` for listing and `/tagset/{name}/` for details
- **Authentication**: Bearer token management with auto-refresh

## Performance & Security

- **🔒 TLS Support**: Configurable TLS versions and certificate validation
- **⚡ Connection Pooling**: Efficient HTTP connection management
- **🛡️ Token Security**: Bearer token management with expiry monitoring
- **📊 Caching**: Intelligent caching of frequently accessed data
- **⏱️ Timeout Protection**: 20-second guardrails prevent hanging operations
- **🚨 Query Limits**: 5-query maximum prevents inefficient usage patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Run the test suite with `make test`
5. Submit a pull request

## License

Apache License 2.0 - see LICENSE file for details.