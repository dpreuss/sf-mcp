"""Configuration management for Starfish MCP server."""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class StarfishConfig(BaseModel):
    """Configuration for Starfish MCP server."""
    
    # Starfish API Configuration
    api_endpoint: str = Field(..., description="Starfish API endpoint URL")
    username: str = Field(..., description="Starfish username")
    password: str = Field(..., description="Starfish password")
    token_timeout_secs: int = Field(57600, description="Token timeout in seconds (default: 16 hours)")
    file_server_url: Optional[str] = Field(None, description="Starfish file server URL")
    
    # Cache Configuration
    cache_ttl_hours: int = Field(1, description="Cache TTL in hours")
    collections_refresh_interval_minutes: int = Field(
        10, description="Collections refresh interval in minutes"
    )
    
    # HTTP Client Configuration
    http_timeout_seconds: int = Field(30, description="HTTP request timeout in seconds")
    max_idle_connections: int = Field(100, description="Maximum idle HTTP connections")
    max_idle_connections_per_host: int = Field(
        10, description="Maximum idle HTTP connections per host"
    )
    
    # TLS Configuration
    tls_insecure_skip_verify: bool = Field(
        False, description="Skip TLS certificate verification"
    )
    tls_min_version: str = Field("1.2", description="Minimum TLS version")
    tls_cert_file: Optional[str] = Field(None, description="TLS certificate file path")
    tls_key_file: Optional[str] = Field(None, description="TLS private key file path")
    
    # Logging
    log_level: str = Field("INFO", description="Log level")
    
    @field_validator("api_endpoint")
    @classmethod
    def validate_api_endpoint(cls, v: str) -> str:
        """Validate and clean API endpoint URL."""
        if not v:
            raise ValueError("API endpoint is required")
        # Remove trailing slash
        return v.rstrip("/")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username."""
        if not v:
            raise ValueError("Username is required")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password."""
        if not v:
            raise ValueError("Password is required")
        return v
    
    @field_validator("token_timeout_secs")
    @classmethod
    def validate_token_timeout(cls, v: int) -> int:
        """Validate token timeout."""
        if v < 0:
            raise ValueError("Token timeout must be non-negative")
        return v
    
    @field_validator("tls_min_version")
    @classmethod
    def validate_tls_version(cls, v: str) -> str:
        """Validate TLS version."""
        if v not in ["1.2", "1.3"]:
            raise ValueError("TLS version must be '1.2' or '1.3'")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


def load_config(env_file: Optional[str] = None) -> StarfishConfig:
    """Load configuration from environment variables and .env file."""
    
    # Load .env file if specified or if .env exists
    if env_file:
        load_dotenv(env_file)
    else:
        # Try to find .env file in current directory or parent directories
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            env_path = parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                break
    
    # Create config from environment variables
    config_data = {
        "api_endpoint": os.getenv("STARFISH_API_ENDPOINT", ""),
        "username": os.getenv("STARFISH_USERNAME", ""),
        "password": os.getenv("STARFISH_PASSWORD", ""),
        "token_timeout_secs": int(os.getenv("STARFISH_TOKEN_TIMEOUT_SECS", "57600")),
        "file_server_url": os.getenv("STARFISH_FILE_SERVER_URL"),
        "cache_ttl_hours": int(os.getenv("CACHE_TTL_HOURS", "1")),
        "collections_refresh_interval_minutes": int(
            os.getenv("COLLECTIONS_REFRESH_INTERVAL_MINUTES", "10")
        ),
        "http_timeout_seconds": int(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
        "max_idle_connections": int(os.getenv("MAX_IDLE_CONNECTIONS", "100")),
        "max_idle_connections_per_host": int(
            os.getenv("MAX_IDLE_CONNECTIONS_PER_HOST", "10")
        ),
        "tls_insecure_skip_verify": os.getenv("TLS_INSECURE_SKIP_VERIFY", "false").lower() == "true",
        "tls_min_version": os.getenv("TLS_MIN_VERSION", "1.2"),
        "tls_cert_file": os.getenv("TLS_CERT_FILE"),
        "tls_key_file": os.getenv("TLS_KEY_FILE"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }
    
    return StarfishConfig(**config_data)
