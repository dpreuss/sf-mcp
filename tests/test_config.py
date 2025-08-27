"""Tests for configuration management."""

import pytest
import os
import tempfile
from pathlib import Path
from starfish_mcp.config import StarfishConfig, load_config


def test_starfish_config_validation():
    """Test StarfishConfig validation."""
    # Valid config
    config = StarfishConfig(
        api_endpoint="https://starfish.example.com/api",
        username="test-user",
        password="test-password"
    )
    assert config.api_endpoint == "https://starfish.example.com/api"
    assert config.username == "test-user"
    assert config.password == "test-password"


def test_api_endpoint_validation():
    """Test API endpoint validation."""
    # Valid endpoints
    config1 = StarfishConfig(
        api_endpoint="https://starfish.example.com/api/",  # Trailing slash should be removed
        username="test-user",
        password="test-password"
    )
    assert config1.api_endpoint == "https://starfish.example.com/api"
    
    # Empty endpoint should fail
    with pytest.raises(ValueError, match="API endpoint is required"):
        StarfishConfig(
            api_endpoint="",
            username="test-user", 
            password="test-password"
        )


def test_username_password_validation():
    """Test username and password validation."""
    # Empty username should fail
    with pytest.raises(ValueError, match="Username is required"):
        StarfishConfig(
            api_endpoint="https://starfish.example.com/api",
            username="",
            password="test-password"
        )
    
    # Empty password should fail
    with pytest.raises(ValueError, match="Password is required"):
        StarfishConfig(
            api_endpoint="https://starfish.example.com/api",
            username="test-user",
            password=""
        )


def test_tls_version_validation():
    """Test TLS version validation."""
    # Valid versions
    config1 = StarfishConfig(
        api_endpoint="https://starfish.example.com/api",
        username="test-user",
        password="test-password",
        tls_min_version="1.2"
    )
    assert config1.tls_min_version == "1.2"
    
    config2 = StarfishConfig(
        api_endpoint="https://starfish.example.com/api",
        username="test-user",
        password="test-password",
        tls_min_version="1.3"
    )
    assert config2.tls_min_version == "1.3"
    
    # Invalid version should fail
    with pytest.raises(ValueError, match="TLS version must be '1.2' or '1.3'"):
        StarfishConfig(
            api_endpoint="https://starfish.example.com/api",
            username="test-user",
            password="test-password",
            tls_min_version="1.1"
        )


def test_log_level_validation():
    """Test log level validation."""
    # Valid levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        config = StarfishConfig(
            api_endpoint="https://starfish.example.com/api",
            username="test-user",
            password="test-password",
            log_level=level.lower()  # Should be converted to uppercase
        )
        assert config.log_level == level
    
    # Invalid level should fail
    with pytest.raises(ValueError, match="Log level must be one of"):
        StarfishConfig(
            api_endpoint="https://starfish.example.com/api",
            username="test-user",
            password="test-password",
            log_level="INVALID"
        )


def test_load_config_from_env():
    """Test loading configuration from environment variables."""
    # Set environment variables
    env_vars = {
        "STARFISH_API_ENDPOINT": "https://test.starfish.com/api",
        "STARFISH_USERNAME": "env-user",
        "STARFISH_PASSWORD": "env-password",
        "STARFISH_TOKEN_TIMEOUT_SECS": "3600",
        "STARFISH_FILE_SERVER_URL": "https://test-files.starfish.com",
        "CACHE_TTL_HOURS": "2",
        "COLLECTIONS_REFRESH_INTERVAL_MINUTES": "15",
        "HTTP_TIMEOUT_SECONDS": "45",
        "TLS_INSECURE_SKIP_VERIFY": "true",
        "TLS_MIN_VERSION": "1.3",
        "LOG_LEVEL": "debug"
    }
    
    # Temporarily set environment variables
    old_values = {}
    for key, value in env_vars.items():
        old_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        config = load_config()
        
        assert config.api_endpoint == "https://test.starfish.com/api"
        assert config.username == "env-user"
        assert config.password == "env-password"
        assert config.token_timeout_secs == 3600
        assert config.file_server_url == "https://test-files.starfish.com"
        assert config.cache_ttl_hours == 2
        assert config.collections_refresh_interval_minutes == 15
        assert config.http_timeout_seconds == 45
        assert config.tls_insecure_skip_verify is True
        assert config.tls_min_version == "1.3"
        assert config.log_level == "DEBUG"
        
    finally:
        # Restore original environment variables
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def test_load_config_from_env_file():
    """Test loading configuration from .env file."""
    env_content = """
# Starfish MCP Server Configuration
STARFISH_API_ENDPOINT=https://file.starfish.com/api
STARFISH_USERNAME=file-user
STARFISH_PASSWORD=file-password
STARFISH_FILE_SERVER_URL=https://file-server.starfish.com
CACHE_TTL_HOURS=3
LOG_LEVEL=ERROR
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        env_file_path = f.name
    
    try:
        config = load_config(env_file_path)
        
        assert config.api_endpoint == "https://file.starfish.com/api"
        assert config.username == "file-user"
        assert config.password == "file-password"
        assert config.file_server_url == "https://file-server.starfish.com"
        assert config.cache_ttl_hours == 3
        assert config.log_level == "ERROR"
        
    finally:
        os.unlink(env_file_path)


def test_load_config_defaults():
    """Test configuration defaults when environment variables are not set."""
    # Clear relevant environment variables
    env_vars_to_clear = [
        "STARFISH_API_ENDPOINT", "STARFISH_USERNAME", "STARFISH_PASSWORD", "STARFISH_TOKEN_TIMEOUT_SECS", "STARFISH_FILE_SERVER_URL",
        "CACHE_TTL_HOURS", "COLLECTIONS_REFRESH_INTERVAL_MINUTES", "HTTP_TIMEOUT_SECONDS",
        "MAX_IDLE_CONNECTIONS", "MAX_IDLE_CONNECTIONS_PER_HOST", "TLS_INSECURE_SKIP_VERIFY",
        "TLS_MIN_VERSION", "LOG_LEVEL"
    ]
    
    old_values = {}
    for var in env_vars_to_clear:
        old_values[var] = os.environ.get(var)
        os.environ.pop(var, None)
    
    # Set required environment variables
    os.environ["STARFISH_API_ENDPOINT"] = "https://required.starfish.com/api"
    os.environ["STARFISH_USERNAME"] = "required-user"
    os.environ["STARFISH_PASSWORD"] = "required-password"
    
    # Change to a temporary directory to avoid loading local .env file
    import tempfile
    original_cwd = os.getcwd()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            config = load_config()
            
            # Check defaults
            assert config.token_timeout_secs == 57600
            assert config.cache_ttl_hours == 1
            assert config.collections_refresh_interval_minutes == 10
            assert config.http_timeout_seconds == 30
            assert config.max_idle_connections == 100
            assert config.max_idle_connections_per_host == 10
            assert config.tls_insecure_skip_verify is False
            assert config.tls_min_version == "1.2"
            assert config.log_level == "INFO"
            assert config.file_server_url is None
        
    finally:
        os.chdir(original_cwd)
        # Restore original environment variables
        for var, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old_value
