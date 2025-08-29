"""
Starfish MCP Tools - Optimal Usage Guide and Prompts

This file contains guidance for AI assistants on how to use Starfish MCP tools effectively.
Add new learnings and patterns here as they are discovered.
"""

STARFISH_QUERY_OPTIMIZATION_GUIDE = """
# Starfish Query Optimization Guide

## Key Principles

1. **Use total_found for counts**: When you need to count files/directories, use `limit: 0` or `limit: 1` 
   and read the `total_found` field from the response. Don't try to count results manually.

2. **Single query for directory analysis**: Use `rec_aggrs` (recursive_aggregates) for directory 
   tree analysis instead of querying each directory individually.

3. **Efficient field selection**: Only request fields you need in `format_fields` to reduce 
   response size and improve performance.

4. **CRITICAL - Rate Limiting Guardrails**: 
   - **Rate limited to 5 queries per 10 seconds by default** (configurable)
   - Uses sliding window - old queries expire automatically 
   - Each query has a 20-second timeout - plan accordingly
   - Use `starfish_get_rate_limit_status` to check remaining queries
   - Use `starfish_reset_rate_limit` if needed for new tasks
   - Prefer broad queries over many narrow ones

5. **Timeout Awareness**: All API calls timeout after 20 seconds. If queries are timing out:
   - Reduce query scope with `volumes_and_paths`
   - Increase `limit` to reduce result processing
   - Use more specific filters to reduce search space

## Common Query Patterns

### Getting Directory Tree Sizes
```python
# Get all root directories with recursive sizes and file counts
{
    "volumes_and_paths": ["volume_name:"],
    "file_type": "d",
    "depth": 1,
    "format_fields": "fn rec_aggrs",
    "sort_by": "-rec_aggrs.size"
}
```

### Counting Files by Tag
```python
# Count files with a specific tag (don't retrieve all files)
{
    "tag": "tag_name",
    "limit": 0,  # or 1 - just need the total_found count
    "format_fields": "fn"  # minimal fields since we only want the count
}
```

### Finding Largest Files
```python
# Get top N largest files
{
    "volumes_and_paths": ["volume_name:"],
    "file_type": "f",
    "limit": 20,
    "format_fields": "parent_path fn size mtime",
    "sort_by": "-size"
}
```

### Analyzing File Distribution
```python
# Get sample of files to understand tag usage patterns
{
    "volumes_and_paths": [],
    "limit": 100,
    "format_fields": "fn tags zones size"
}
```

## Important Field Names

### Core Fields
- `fn` - filename (not `name`)
- `size` - file/directory size in bytes
- `parent_path` - directory path
- `file_type` - f=file, d=directory, l=symlink, etc.

### Recursive Aggregates (rec_aggrs becomes recursive_aggregates in output)
- `recursive_aggregates.size` - total logical size of directory tree
- `recursive_aggregates.files` - total file count in directory tree
- `recursive_aggregates.dirs` - total directory count in directory tree
- `recursive_aggregates.blocks` - total blocks used

### Time Fields
- `mtime` - modification time
- `atime` - access time  
- `ctime` - change time (metadata)

### Tags and Organization
- `tags` - array of tags applied to file/directory
- `zones` - storage zone information

## Performance Tips

1. **Use depth limits**: For directory analysis, use `depth: 1` to get immediate children only
2. **Limit results appropriately**: Use reasonable limits based on what you need to display
3. **Sort efficiently**: Sort by the field you care about most (e.g., `-size` for largest first)
4. **Use specific volume paths**: Target specific volumes when possible instead of searching everything

## Common Mistakes to Avoid

1. **Don't query each directory individually** for size analysis - use rec_aggrs instead
2. **Don't set high limits when you only need counts** - use limit: 0 and read total_found
3. **Don't use `name` field** - it's `fn` (filename) in Starfish
4. **Don't manually sum file sizes** - recursive_aggregates gives you the totals
5. **Don't confuse logical vs physical sizes** - rec_aggrs.size is logical size

## 🚨 CRITICAL GUARDRAILS - NEVER VIOLATE THESE

6. **🚨 RATE LIMIT: 5 queries per 10 seconds** - Use sliding window, old queries expire automatically
7. **🚨 NEVER query each volume individually** - Use broad queries instead
8. **🚨 NEVER iterate through directories** - Use filters and patterns instead
9. **🚨 TIMEOUT AWARENESS** - All queries timeout after 20 seconds
10. **🚨 CHECK RATE LIMIT STATUS** - Use `starfish_get_rate_limit_status` to see remaining queries

### Query Limit Examples

❌ **BAD: Volume-by-volume analysis (5+ queries)**
```python
# Don't do this!
for volume in volumes:
    starfish_query(volumes_and_paths=[f"{volume}:"])
```

✅ **GOOD: Single comprehensive query (1 query)**
```python
# Do this instead!
starfish_query(volumes_and_paths=[], format_fields="fn rec_aggrs")
```

❌ **BAD: Directory crawling (10+ queries)**
```python
# Don't do this!
for directory in directories:
    starfish_query(volumes_and_paths=[f"volume:{directory}"])
```

✅ **GOOD: Pattern-based filtering (1 query)**
```python
# Do this instead!
starfish_query(path="target*", volumes_and_paths=["volume:"])
```

## Tag Analysis Workflow

When analyzing tags:
1. Get a sample of files to see what tags exist: query with limit ~100, format_fields="fn tags"
2. For each interesting tag, count files: query with that tag, limit=0, read total_found
3. Present results sorted by file count (descending)

## Volume Analysis Workflow

When analyzing volume contents:
1. List volumes first to see what's available
2. Query root directories with rec_aggrs to get tree sizes
3. Sort by recursive_aggregates.size to find largest subtrees
4. Optionally drill down into specific large directories for details
"""

STARFISH_TOOL_PROMPTS = {
    "starfish_query": """
When using starfish_query, remember:

- Use `total_found` from the response to get counts, don't count results manually
- For directory analysis, use `rec_aggrs` field and sort by `-rec_aggrs.size` 
- Use `fn` for filename, not `name`
- Set appropriate limits: use limit=0 when you only need counts
- Use `depth: 1` for immediate children of a directory
- Field name `rec_aggrs` in the API becomes `recursive_aggregates` in the output
- `recursive_aggregates.size` gives logical size, `recursive_aggregates.files` gives file count

Example efficient queries:
- Directory tree analysis: file_type="d", depth=1, format_fields="fn rec_aggrs", sort_by="-rec_aggrs.size"
- Tag counting: tag="tag_name", limit=0, format_fields="fn"
- Largest files: file_type="f", sort_by="-size", format_fields="parent_path fn size"
""",

    "starfish_list_volumes": """
Use this to discover available volumes before running queries. 
Each volume has a name (for queries) and display_name (for presentation).
""",

    "starfish_list_zones": """
Use this to understand storage zones and data organization.
Zones provide logical groupings and access control.
""",

    "starfish_get_zone": """
Use this to get detailed information about a specific zone by ID.
Get zone IDs from starfish_list_zones first.
Shows managers, tagsets, paths, and aggregated statistics.
""",

    "starfish_get_volume": """
Use this to get detailed information about a specific volume by ID.
Get volume IDs from starfish_list_volumes first.
Shows capacity, mount points, size info, and configuration.
""",

    "starfish_list_tagsets": """
Use this to see all available tagsets with tag counts and zone information.
Better than starfish_list_tags as it shows actual tagset structure.
""",

    "starfish_get_tagset": """
Use this to get complete details about a specific tagset including all tags.
Use tagset names from starfish_list_tagsets.
""",

    "starfish_list_tags": """
Legacy tool - use starfish_list_tagsets instead for better information.
Only returns tagset names without counts or structure details.
""",

    "starfish_get_rate_limit_status": """
Use this to check current rate limiting status.
Shows current queries, remaining queries, time window, and time to reset.
Useful for understanding why queries might be blocked.
""",

    "starfish_reset_rate_limit": """
Use this to reset the rate limiter when starting a completely new task.
Clears the query history and allows full query quota again.
Only use when switching to a different problem/analysis.
"""
}

def get_optimization_guide():
    """Return the optimization guide for AI assistants."""
    return STARFISH_QUERY_OPTIMIZATION_GUIDE

def get_tool_prompt(tool_name):
    """Get specific prompt/guidance for a tool."""
    return STARFISH_TOOL_PROMPTS.get(tool_name, "")

def get_all_prompts():
    """Get all prompts for inclusion in AI assistant context."""
    return {
        "optimization_guide": STARFISH_QUERY_OPTIMIZATION_GUIDE,
        "tool_prompts": STARFISH_TOOL_PROMPTS
    }
