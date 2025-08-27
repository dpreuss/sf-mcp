# Starfish MCP Server

An MCP (Model Context Protocol) server for Starfish Storage integration. This server provides tools for querying files, managing volumes, and working with tags through the Starfish API.

## Features

- **File Search**: Find files by name, tags, or directory location
- **Volume Management**: List and inspect Starfish volumes
- **Collection Support**: Work with Starfish Collections (tagged datasets)
- **Zone Management**: List and inspect Starfish zones with detailed information
- **Advanced Queries**: Execute complex Starfish queries with full parameter control
- **Authentication**: Username/password authentication with automatic token refresh
- **Caching**: Intelligent caching of frequently accessed data
- **Error Handling**: Comprehensive error handling and logging

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

## Usage

### Running the MCP Server

```bash
# Run directly
python -m starfish_mcp.server

# Or use the console script
starfish-mcp
```

### Available Tools

The server provides the following MCP tools:

#### 1. `starfish_find_file`
Find files by filename pattern.

```json
{
  "filename": "foo",
  "collection": "Documents",
  "limit": 100
}
```

#### 2. `starfish_find_by_tag`
Find files with specific tags.

```json
{
  "tag": "bar",
  "collection": "TestData",
  "limit": 100
}
```

#### 3. `starfish_find_in_directory`
Find files in a directory path.

```json
{
  "directory_path": "/baz",
  "recursive": true,
  "limit": 100
}
```

#### 4. `starfish_query_advanced`
Execute advanced Starfish queries.

```json
{
  "query": "type=f size>1MB tag=important",
  "format_fields": "fn size mt volume tags_explicit",
  "limit": 1000,
  "sort_by": "size"
}
```

#### 5. `starfish_list_volumes`
List all available volumes.

```json
{}
```

#### 6. `starfish_list_collections`
List available collections.

```json
{
  "force_refresh": false
}
```

#### 7. `starfish_get_tagset`
Get tags from a specific tagset.

```json
{
  "tagset_name": "Collections",
  "limit": 1000,
  "with_private": true
}
```

#### 8. `starfish_list_zones`
List all available zones with detailed information.

```json
{}
```

## Development

### Testing

The project includes comprehensive tests:

```bash
# Run unit tests (uses mock Starfish API)
pytest tests/test_*.py -v

# Run integration tests (requires real Starfish instance)
# Set integration environment variables first:
export STARFISH_INTEGRATION_API_ENDPOINT="https://your-starfish.com/api"
export STARFISH_INTEGRATION_BEARER_TOKEN="sf-api-v1:your-token"

pytest tests/test_integration.py -v -m integration
```

### Mock Test Harness

For development without a Starfish server, the project includes a comprehensive mock test harness that simulates realistic Starfish API responses:

```python
from tests.conftest import MockStarfishClient

# Use mock client for testing
mock_client = MockStarfishClient(sample_entries, sample_volumes, ...)
response = await mock_client.query("tag=test")
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

- **`config.py`**: Configuration management with environment variable support
- **`models.py`**: Pydantic models for Starfish API data structures
- **`client.py`**: Async HTTP client with authentication and caching
- **`tools.py`**: MCP tool implementations
- **`server.py`**: Main MCP server with message handling
- **`tests/`**: Comprehensive test suite with mock harness

## API Compatibility

This MCP server is designed to work with the Starfish API as implemented in the versitygw project. It supports:

- Query API: `/query/` endpoint with filtering and formatting
- Volumes API: `/volume/` endpoint for volume discovery
- Collections API: `/tagsets/Collections:/tags` for collection discovery
- Tagset API: `/tagset/{name}/` for tag enumeration

## Error Handling

The server provides detailed error messages and logging:

- **Authentication errors**: Invalid or expired bearer tokens
- **API errors**: Starfish API failures with error codes
- **Network errors**: Connection and timeout issues
- **Query errors**: Invalid query syntax or parameters

## Performance

- **Connection pooling**: Efficient HTTP connection management
- **Caching**: Collections and query result caching
- **Token management**: Automatic token expiry monitoring
- **Async operations**: Non-blocking I/O for all API calls

## Security

- **TLS support**: Configurable TLS versions and certificate validation
- **Token security**: Bearer token management with expiry warnings
- **Input validation**: Comprehensive input validation for all tools
- **Error sanitization**: Safe error message handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Run the test suite
5. Submit a pull request

## License

Apache License 2.0 - see LICENSE file for details.
