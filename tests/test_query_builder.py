"""Tests specifically for the query builder module."""

import pytest
from starfish_mcp.tools.query_builder import build_starfish_query, extract_query_metadata


class TestBasicParameters:
    """Test basic search parameters."""
    
    def test_name_patterns(self):
        """Test name pattern handling."""
        # Exact match
        args = {"name": "config.json"}
        query = build_starfish_query(args)
        assert query == "name=config.json"
        
        # Wildcard pattern
        args = {"name": "*.pdf"}
        query = build_starfish_query(args)
        assert query == "name=*.pdf"
        
        # Regex pattern (detected by special chars)
        args = {"name": "^config.*\\.json$"}
        query = build_starfish_query(args)
        assert query == "name-re=^config.*\\.json$"
    
    def test_name_regex(self):
        """Test explicit name regex."""
        # Without ^ prefix
        args = {"name_regex": ".*\\.pdf$"}
        query = build_starfish_query(args)
        assert query == "name-re=^.*\\.pdf$"
        
        # With ^ prefix 
        args = {"name_regex": "^config.*"}
        query = build_starfish_query(args)
        assert query == "name-re=^config.*"
    
    def test_path_patterns(self):
        """Test path pattern handling."""
        args = {"path": "/home/user"}
        query = build_starfish_query(args)
        assert query == "ppath=/home/user"
        
        args = {"path_regex": "home.*"}
        query = build_starfish_query(args)
        assert query == "ppath-re=^home.*"
    
    def test_file_attributes(self):
        """Test file attribute parameters."""
        args = {
            "file_type": "f",
            "ext": "pdf",
            "empty": True,
            "inode": 12345
        }
        query = build_starfish_query(args)
        
        assert "type=f" in query
        assert "ext=pdf" in query
        assert "empty" in query
        assert "inode=12345" in query
        
        # Test empty=False (should not appear)
        args = {"empty": False}
        query = build_starfish_query(args)
        assert "empty" not in query


class TestOwnershipParameters:
    """Test ownership and permission parameters."""
    
    def test_numeric_ids(self):
        """Test UID/GID numeric parameters."""
        args = {"uid": 1001, "gid": 100}
        query = build_starfish_query(args)
        
        assert "uid=1001" in query
        assert "gid=100" in query
        
        # Test uid=0 (root)
        args = {"uid": 0}
        query = build_starfish_query(args)
        assert "uid=0" in query
    
    def test_username_patterns(self):
        """Test username parameters."""
        args = {
            "username": "alice",
            "username_regex": "admin.*"
        }
        query = build_starfish_query(args)
        
        assert "username=alice" in query
        assert "username-re=^admin.*" in query
    
    def test_groupname_patterns(self):
        """Test groupname parameters."""
        args = {
            "groupname": "wheel",
            "groupname_regex": "admin.*"
        }
        query = build_starfish_query(args)
        
        assert "groupname=wheel" in query
        assert "groupname-re=^admin.*" in query
    
    def test_case_insensitive_versions(self):
        """Test case-insensitive username/groupname."""
        args = {
            "iname": "CONFIG.json",
            "iusername": "ALICE",
            "igroupname": "WHEEL"
        }
        query = build_starfish_query(args)
        
        assert "iname=CONFIG.json" in query
        assert "iusername=ALICE" in query
        assert "igroupname=WHEEL" in query


class TestSizeAndLinkParameters:
    """Test size and link count parameters."""
    
    def test_size_filters(self):
        """Test various size filter formats."""
        test_cases = [
            ("100", "size=100"),                    # Exact size
            (">1MB", "size=>1MB"),                  # Greater than
            ("<=500KB", "size=<=500KB"),            # Less than or equal
            ("10M-2G", "size=10M-2G"),             # Range
            ("eq:100KB", "size=eq:100KB"),         # Equality operator
            ("gt:1GB", "size=gt:1GB"),             # Greater than operator
        ]
        
        for size_input, expected in test_cases:
            args = {"size": size_input}
            query = build_starfish_query(args)
            assert expected in query
    
    def test_nlinks_filters(self):
        """Test hard link count filters."""
        test_cases = [
            ("1", "nlinks=1"),                      # Exact count
            ("2-5", "nlinks=2-5"),                  # Range
            ("gte:3", "nlinks=gte:3"),             # Greater than or equal
            ("lt:10", "nlinks=lt:10"),             # Less than
        ]
        
        for nlinks_input, expected in test_cases:
            args = {"nlinks": nlinks_input}
            query = build_starfish_query(args)
            assert expected in query


class TestDepthParameters:
    """Test directory depth parameters."""
    
    def test_depth_filters(self):
        """Test depth filtering."""
        args = {"depth": 2}
        query = build_starfish_query(args)
        assert "depth=2" in query
        
        # Test depth=0 (root level)
        args = {"depth": 0}
        query = build_starfish_query(args)
        assert "depth=0" in query
    
    def test_maxdepth_filters(self):
        """Test maximum depth filtering."""
        args = {"maxdepth": 5}
        query = build_starfish_query(args)
        assert "maxdepth=5" in query
    
    def test_combined_depth_filters(self):
        """Test depth and maxdepth together."""
        args = {"depth": 1, "maxdepth": 3}
        query = build_starfish_query(args)
        
        assert "depth=1" in query
        assert "maxdepth=3" in query


class TestPermissionParameters:
    """Test permission filtering."""
    
    def test_permission_formats(self):
        """Test various permission formats."""
        test_cases = [
            ("644", "perm=644"),                    # Octal exact
            ("-u=r", "perm=-u=r"),                  # At least user read
            ("/222", "perm=/222"),                  # Any write permission
            ("g=w", "perm=g=w"),                    # Group write exact
        ]
        
        for perm_input, expected in test_cases:
            args = {"perm": perm_input}
            query = build_starfish_query(args)
            assert expected in query


class TestTimeParameters:
    """Test time filtering parameters."""
    
    def test_mtime_filters(self):
        """Test modification time filters."""
        test_cases = [
            ("-1d", "mtime=-1d"),                   # Within 1 day
            ("+30d", "mtime=+30d"),                 # Older than 30 days
            ("2024-01-01", "mtime=2024-01-01"),     # Since specific date
            ("1-7d", "mtime=1-7d"),                 # Range
            ("inf-1w", "mtime=inf-1w"),             # Infinite to 1 week ago
        ]
        
        for time_input, expected in test_cases:
            args = {"mtime": time_input}
            query = build_starfish_query(args)
            assert expected in query
    
    def test_ctime_filters(self):
        """Test change time filters."""
        args = {"ctime": "-2h"}
        query = build_starfish_query(args)
        assert "ctime=-2h" in query
    
    def test_atime_filters(self):
        """Test access time filters."""
        args = {"atime": "+30d"}
        query = build_starfish_query(args)
        assert "atime=+30d" in query
    
    def test_combined_time_filters(self):
        """Test multiple time filters together."""
        args = {
            "mtime": "-1d",
            "atime": "+7d"
        }
        query = build_starfish_query(args)
        
        assert "mtime=-1d" in query
        assert "atime=+7d" in query


class TestQueryOptions:
    """Test query option flags."""
    
    def test_boolean_flags(self):
        """Test boolean query options."""
        args = {
            "search_all": True,
            "versions": True,
            "children_only": True,
            "root_only": True
        }
        query = build_starfish_query(args)
        
        assert "search-all" in query
        assert "versions" in query
        assert "children-only" in query
        assert "root-only" in query
    
    def test_false_flags_not_included(self):
        """Test that False boolean flags are not included."""
        args = {
            "search_all": False,
            "versions": False,
            "children_only": False,
            "root_only": False
        }
        query = build_starfish_query(args)
        
        assert "search-all" not in query
        assert "versions" not in query
        assert "children-only" not in query
        assert "root-only" not in query


class TestTagParameters:
    """Test tag filtering parameters."""
    
    def test_tag_filters(self):
        """Test tag filtering."""
        args = {"tag": "important"}
        query = build_starfish_query(args)
        assert "tag=important" in query
        
        # Test tag with spaces (AND logic)
        args = {"tag": "important project"}
        query = build_starfish_query(args)
        assert "tag=important project" in query
    
    def test_explicit_tag_filters(self):
        """Test explicit tag filtering."""
        args = {"tag_explicit": "archived"}
        query = build_starfish_query(args)
        assert "tag-explicit=archived" in query


class TestScopeParameters:
    """Test search scope parameters."""
    
    def test_zone_filter(self):
        """Test zone filtering."""
        args = {"zone": "production"}
        query = build_starfish_query(args)
        assert "zone=production" in query


class TestComprehensiveQueries:
    """Test complex combinations of parameters."""
    
    def test_real_world_search_1(self):
        """Test: Find large PDF files owned by admin users, modified recently."""
        args = {
            "ext": "pdf",
            "size": ">10MB",
            "username_regex": "admin.*",
            "mtime": "-7d",
            "file_type": "f"
        }
        query = build_starfish_query(args)
        
        expected_parts = [
            "type=f",
            "ext=pdf", 
            "size=>10MB",
            "username-re=^admin.*",
            "mtime=-7d"
        ]
        
        for part in expected_parts:
            assert part in query
    
    def test_real_world_search_2(self):
        """Test: Find empty directories in specific paths, show all versions."""
        args = {
            "file_type": "d",
            "empty": True,
            "path_regex": "/tmp/.*",
            "versions": True,
            "maxdepth": 3
        }
        query = build_starfish_query(args)
        
        expected_parts = [
            "type=d",
            "empty",
            "ppath-re=^/tmp/.*",
            "versions",
            "maxdepth=3"
        ]
        
        for part in expected_parts:
            assert part in query
    
    def test_real_world_search_3(self):
        """Test: Find config files with specific permissions, case-insensitive."""
        args = {
            "iname": "config.*",
            "perm": "644",
            "uid": 0,
            "children_only": True
        }
        query = build_starfish_query(args)
        
        expected_parts = [
            "iname=config.*",
            "perm=644",
            "uid=0",
            "children-only"
        ]
        
        for part in expected_parts:
            assert part in query
    
    def test_all_parameters_combined(self):
        """Test query with as many parameters as possible."""
        args = {
            "name": "test.*",
            "file_type": "f",
            "ext": "txt",
            "uid": 1001,
            "gid": 100,
            "size": ">1KB",
            "nlinks": "1",
            "depth": 2,
            "perm": "644",
            "mtime": "-1d",
            "search_all": True,
            "tag": "important"
        }
        query = build_starfish_query(args)
        
        # Should contain all the specified parameters
        expected_parts = [
            "name=test.*", "type=f", "ext=txt", "uid=1001", "gid=100",
            "size=>1KB", "nlinks=1", "depth=2", "perm=644", "mtime=-1d",
            "search-all", "tag=important"
        ]
        
        for part in expected_parts:
            assert part in query


class TestMetadataExtraction:
    """Test query metadata extraction."""
    
    def test_metadata_extraction(self):
        """Test that metadata extraction preserves all parameters."""
        args = {
            "name": "test.txt",
            "size": ">1MB",
            "uid": 1001,
            "search_all": True,
            "nonexistent_param": "should_be_none"  # This shouldn't appear
        }
        
        metadata = extract_query_metadata(args)
        
        # Check preserved parameters
        assert metadata["name"] == "test.txt"
        assert metadata["size"] == ">1MB"
        assert metadata["uid"] == 1001
        assert metadata["search_all"] is True
        
        # Check unspecified parameters are None
        assert metadata["gid"] is None
        assert metadata["ext"] is None
        assert metadata["versions"] is None
        
        # Check that non-standard parameters are not included
        assert "nonexistent_param" not in metadata
    
    def test_metadata_all_parameters(self):
        """Test metadata extraction with all possible parameters."""
        args = {
            "name": "test", "name_regex": "^test.*", "path": "/home", "path_regex": "^/home.*",
            "file_type": "f", "ext": "txt", "empty": True, "uid": 1001, "gid": 100,
            "username": "alice", "username_regex": "^alice.*", "groupname": "users", 
            "groupname_regex": "^users.*", "inode": 12345, "size": ">1MB", "nlinks": "1",
            "iname": "TEST", "iusername": "ALICE", "igroupname": "USERS",
            "depth": 2, "maxdepth": 5, "perm": "644", "mtime": "-1d", "ctime": "-2h", 
            "atime": "+30d", "search_all": True, "versions": True, "children_only": True,
            "root_only": False, "tag": "important", "tag_explicit": "archived", "zone": "prod"
        }
        
        metadata = extract_query_metadata(args)
        
        # Verify all parameters are preserved exactly
        for key, expected_value in args.items():
            assert metadata[key] == expected_value, f"Parameter {key} not preserved correctly"
