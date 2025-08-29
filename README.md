# Starfish MCP Server

A production-ready MCP (Model Context Protocol) server for Starfish Storage integration. Compatible with Claude Desktop, Cursor IDE, Gemini CLI, and other MCP clients. Provides comprehensive file search, storage management, and data analysis tools with intelligent performance guardrails.

## Features

- **🔍 Advanced File Search**: Comprehensive search with 19+ filter parameters (name, size, timestamps, permissions, tags)
- **📁 Volume & Zone Management**: List and inspect Starfish volumes and zones with detailed metadata
- **🏷️ Tagset Support**: Full tagset management with tag counts and zone associations
- **⚡ Optimized Queries**: Built-in query optimization with recursive aggregates for directory analysis
- **🚨 Smart Rate Limiting**: Configurable sliding window rate limiting (5 queries/10s default) with automatic expiry
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

## MCP Client Configuration

This server is compatible with multiple MCP clients. Choose your client below:

### Cursor IDE

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
      "cwd": "/path/to/sf-mcp",
      "env": {
        "STARFISH_API_ENDPOINT": "https://sf-redashdev.sfish.dev/api",
        "STARFISH_USERNAME": "demo", 
        "STARFISH_PASSWORD": "demo"
      }
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop MCP configuration file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "starfish": {
      "command": "/path/to/sf-mcp/venv/bin/python",
      "args": ["-m", "starfish_mcp.server"],
      "cwd": "/path/to/sf-mcp",
      "env": {
        "STARFISH_API_ENDPOINT": "https://sf-redashdev.sfish.dev/api",
        "STARFISH_USERNAME": "demo",
        "STARFISH_PASSWORD": "demo",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Gemini CLI

Add to your Gemini CLI configuration:

```json
{
  "mcpServers": {
    "starfish": {
      "command": "/path/to/sf-mcp/venv/bin/python",
      "args": ["-m", "starfish_mcp.server"],
      "cwd": "/path/to/sf-mcp",
      "env": {
        "STARFISH_API_ENDPOINT": "https://sf-redashdev.sfish.dev/api",
        "STARFISH_USERNAME": "demo",
        "STARFISH_PASSWORD": "demo",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Note:** Replace `/path/to/sf-mcp` with your actual installation path.

## Available Tools

### 🔍 Core Search Tool

#### `starfish_query` - Comprehensive File Search
The main tool with 19 filter parameters and built-in guardrails.

**Key Features:**
- 🚨 **Smart Rate Limiting**: Sliding window (5 queries/10s), auto-expiry, configurable
- ⏱️ **Timeout Protection**: 20-second timeout per query with proper error handling  
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

#### `starfish_get_rate_limit_status` - Check Rate Limit Status
Get current rate limiting status including remaining queries and time to reset.

#### `starfish_reset_rate_limit` - Reset Rate Limiter  
Reset the rate limiter when starting a new task or analysis.

## 🚨 Performance Guardrails

### Smart Rate Limiting
- **Sliding Window**: 5 queries per 10 seconds (default, configurable)
- **Automatic Expiry**: Old queries drop off naturally as time passes
- **Real-time Status**: Check remaining quota with `starfish_get_rate_limit_status`
- **Manual Reset**: Use `starfish_reset_rate_limit` for new tasks
- **20-second timeout** on all API calls with proper error handling

### Rate Limiting Configuration

Customize rate limiting behavior via environment variables:

```bash
# Default configuration (5 queries per 10 seconds)
RATE_LIMIT_MAX_QUERIES=5
RATE_LIMIT_TIME_WINDOW_SECONDS=10
RATE_LIMIT_ENABLED=true

# For development (more relaxed)
RATE_LIMIT_MAX_QUERIES=10
RATE_LIMIT_TIME_WINDOW_SECONDS=30

# For production (more strict)  
RATE_LIMIT_MAX_QUERIES=3
RATE_LIMIT_TIME_WINDOW_SECONDS=5

# Disable entirely for testing
RATE_LIMIT_ENABLED=false
```

### 🚨 1000-Row Warning - Incorrect Results Indicator

**If you get exactly 1000 rows back, your approach is WRONG!**

This indicates you hit the default limit and received incomplete data:

- **For directory analysis**: Use `file_type="d"` with `rec_aggrs` field
- **For file counts**: Use `limit=0` and read `total_found` from response  
- **For large datasets**: Add specific filters (`size`, `mtime`, `zones`, `tags`)
- **Never trust 1000-row results** for aggregation or analysis

**Example - Wrong vs Right:**

❌ **WRONG** (returns 1000 rows, incomplete):
```json
{"volumes_and_paths": ["prod:"], "limit": 1000}
```

✅ **RIGHT** (returns directory sizes with rec_aggrs):
```json
{"volumes_and_paths": ["prod:"], "file_type": "d", "depth": 1, "format_fields": "fn rec_aggrs", "sort_by": "-rec_aggrs.size"}
```

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