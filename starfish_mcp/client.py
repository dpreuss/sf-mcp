"""Starfish API client with authentication and caching."""

import asyncio
import ssl
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode
import aiohttp
import structlog

from .models import (
    StarfishEntry, VolumeInfo, StarfishError, StarfishAuthRequest,
    StarfishAuthResponse, StarfishZoneDetails, StarfishTagsResponse
)
from .config import StarfishConfig

logger = structlog.get_logger(__name__)


class TokenManager:
    """Manages bearer token authentication and refresh."""
    
    def __init__(self, config: StarfishConfig):
        self.config = config
        self.token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self) -> None:
        """Ensure we have an active session."""
        if self.session is None or self.session.closed:
            # Create SSL context that accepts self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
    
    async def get_token(self) -> str:
        """Get a valid bearer token, refreshing if necessary."""
        if self._token_needs_refresh():
            await self._refresh_token()
        
        if not self.token:
            raise StarfishError(
                code="AUTHENTICATION_FAILED",
                message="Failed to obtain bearer token"
            )
        
        return self.token
    
    def _token_needs_refresh(self) -> bool:
        """Check if token needs refresh (expired or expires soon)."""
        if not self.token or not self.expires_at:
            return True
        
        # Refresh 5 minutes before expiry
        buffer = timedelta(minutes=5)
        return datetime.now() >= (self.expires_at - buffer)
    
    async def _refresh_token(self) -> None:
        """Refresh the bearer token using username/password."""
        await self._ensure_session()
        
        auth_request = StarfishAuthRequest(
            username=self.config.username,
            password=self.config.password,
            token_timeout_secs=self.config.token_timeout_secs,
            token_description="Starfish MCP Server",
            auto_generated=True
        )
        
        logger.info(
            "Refreshing bearer token",
            username=self.config.username,
            token_timeout_hours=self.config.token_timeout_secs / 3600
        )
        
        try:
            async with self.session.post(
                f"{self.config.api_endpoint.rstrip('/')}/auth/",
                json=auth_request.model_dump(),
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise StarfishError(
                        code="AUTHENTICATION_FAILED",
                        message=f"Authentication failed: {response.status}",
                        details={"response": error_text}
                    )
                
                try:
                    auth_data = await response.json()
                except Exception:
                    # Handle case where response might be plain text token
                    auth_text = await response.text()
                    if auth_text and "sf-api-v1:" in auth_text:
                        self.token = auth_text.strip()
                    else:
                        raise StarfishError(
                            code="AUTHENTICATION_FAILED",
                            message="Invalid authentication response format"
                        )
                else:
                    # Handle various JSON response formats
                    if isinstance(auth_data, dict):
                        if "token" in auth_data:
                            self.token = auth_data["token"]
                        elif "access_token" in auth_data:
                            self.token = auth_data["access_token"]
                        else:
                            raise StarfishError(
                                code="AUTHENTICATION_FAILED",
                                message="No token found in authentication response"
                            )
                    elif isinstance(auth_data, str):
                        self.token = auth_data
                    else:
                        raise StarfishError(
                            code="AUTHENTICATION_FAILED",
                            message="Unexpected authentication response format"
                        )
                
                # Set expiration time
                self.expires_at = datetime.now() + timedelta(
                    seconds=self.config.token_timeout_secs
                )
                
                logger.info(
                    "Bearer token refreshed successfully",
                    expires_at=self.expires_at.isoformat()
                )
                
        except aiohttp.ClientError as e:
            raise StarfishError(
                code="AUTHENTICATION_FAILED",
                message="Failed to connect for authentication",
                details={"error": str(e)}
            )
    
    async def close(self) -> None:
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()


class StarfishClient:
    """Async HTTP client for Starfish API."""
    
    def __init__(self, config: StarfishConfig):
        self.config = config
        self.token_manager = TokenManager(config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure we have an active session."""
        if self.session is None or self.session.closed:
            # Create SSL context that accepts self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
    
    async def _request(self, method: str, endpoint: str, 
                      params: Optional[Dict[str, Any]] = None,
                      timeout_seconds: int = 20,
                      **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Starfish API with timeout guardrail."""
        await self._ensure_session()
        
        # Get valid token
        token = await self.token_manager.get_token()
        
        # Build URL
        url = f"{self.config.api_endpoint.rstrip('/')}{endpoint}"
        
        # Set headers
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
        
        try:
            logger.debug(
                "Making API request with timeout",
                method=method,
                url=url if not params else url,
                params=params,
                timeout_seconds=timeout_seconds
            )
            
            # Apply timeout guardrail
            async with asyncio.wait_for(
                self.session.request(
                    method, url, params=params, headers=headers, **kwargs
                ), timeout=timeout_seconds
            ) as response:
                
                logger.debug(
                    "API response received",
                    status=response.status,
                    content_type=response.content_type
                )
                
                if response.status in (200, 202):
                    if response.content_type == "application/json":
                        return await response.json()
                    else:
                        # Handle non-JSON responses
                        text = await response.text()
                        try:
                            import json
                            return json.loads(text)
                        except:
                            return {"text": text}
                else:
                    error_text = await response.text()
                    try:
                        import json
                        error_data = json.loads(error_text)
                        if isinstance(error_data, dict) and "error" in error_data:
                            raise StarfishError(
                                code="API_ERROR",
                                message=f"API request failed: {error_data}",
                                details=error_data
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass
                    
                    raise StarfishError(
                        code="API_ERROR",
                        message=f"API request failed: HTTP {response.status}",
                        details={"status": response.status, "response": error_text}

                    )
                
        except asyncio.TimeoutError:
            logger.error(
                "API request timed out",
                method=method,
                endpoint=endpoint,
                timeout_seconds=timeout_seconds
            )
            raise StarfishError(
                code="REQUEST_TIMEOUT",
                message=f"API request timed out after {timeout_seconds} seconds",
                details={"timeout_seconds": timeout_seconds, "endpoint": endpoint}
            )
        except aiohttp.ClientError as e:
            raise StarfishError(
                code="CONNECTION_FAILED",
                message="Failed to connect to Starfish API",
                details={"error": str(e)}
            )
    
    async def async_query(self, volumes_and_paths: List[str] = None,
                         queries: List[str] = None, format_fields: str = None,
                         limit: int = None, sort_by: str = None,
                         async_after_sec: float = 5.0,
                         timeout: int = 300) -> List[StarfishEntry]:
        """Execute async query against Starfish API (more powerful endpoint).
        
        Args:
            volumes_and_paths: List of volume:path specifications
            queries: List of query strings (if empty, returns all entries in volumes_and_paths)
            format_fields: Fields to return
            limit: Maximum number of entries
            sort_by: Sort specification
            async_after_sec: Seconds to wait before going async (5.0 recommended)
            timeout: Maximum time to wait for results
        """
        
        # Build request body for async query based on official API docs
        body = {
            "volumes_and_paths": volumes_and_paths or [],
            "queries": queries or [],  # Empty list means get all entries
            "format": format_fields or "parent_path fn type size blck ct mt at uid gid mode tags_explicit tags_inherited volume",
            "async_after_sec": async_after_sec,
            "output_format": "json",
            "pretty_json": True,
            "force_tag_inherit": False,
            "without_private_tags": True
        }
        
        # Add optional parameters only if provided
        if sort_by:
            body["sort_by"] = sort_by
        if limit:
            body["limit"] = limit
        
        logger.info(
            "Executing Starfish async query",
            volumes_and_paths=volumes_and_paths,
            queries=queries,
            format_fields=format_fields
        )
        
        try:
            # Submit async query
            async_response = await self._request("POST", "/async/query/", json=body)
            
            # Handle immediate response (200) vs async response (202)
            if isinstance(async_response, list):
                # Query completed immediately (200 response)
                entries = [StarfishEntry(**entry_data) for entry_data in async_response]
                logger.info("Async query completed immediately", total_entries=len(entries))
                return entries
            
            # Async response (202) - need to poll for results
            if "query_id" not in async_response:
                raise StarfishError(
                    code="ASYNC_QUERY_FAILED",
                    message="Async query did not return query_id",
                    details={"response": str(async_response)}
                )
            
            query_id = async_response["query_id"]
            logger.info("Async query submitted", query_id=query_id)
            
            # Poll for completion using the status endpoint
            import asyncio
            poll_interval = 2  # Poll every 2 seconds
            max_attempts = timeout // poll_interval
            
            for attempt in range(max_attempts):
                await asyncio.sleep(poll_interval)
                
                try:
                    # Check query status
                    status_response = await self._request("GET", f"/async/query/{query_id}")
                    
                    is_done = status_response.get("is_done", False)
                    logger.debug("Query status check", query_id=query_id, is_done=is_done, attempt=attempt+1)
                    
                    if is_done:
                        # Query is complete, get results from the location
                        location = status_response.get("location", f"/async/query_result/{query_id}")
                        
                        # Get results with proper error handling for 400 (not finished yet)
                        try:
                            result_response = await self._request("GET", location)
                        except StarfishError as e:
                            if "400" in str(e) or "not finished yet" in str(e).lower():
                                # Despite is_done=true, results aren't ready yet (rare race condition)
                                logger.debug("Results not ready despite is_done=true", query_id=query_id)
                                continue
                            else:
                                # Try fallback to standard result endpoint
                                try:
                                    result_response = await self._request("GET", f"/async/query_result/{query_id}")
                                except StarfishError as e2:
                                    if "400" in str(e2) or "not finished yet" in str(e2).lower():
                                        logger.debug("Fallback also shows not ready", query_id=query_id)
                                        continue
                                    raise e2
                        
                        if isinstance(result_response, list):
                            entries = [StarfishEntry(**entry_data) for entry_data in result_response]
                            logger.info("Async query completed", total_entries=len(entries), query_id=query_id)
                            return entries
                        else:
                            raise StarfishError(
                                code="ASYNC_QUERY_FAILED",
                                message="Query completed but result format unexpected",
                                details={"result": str(result_response)}
                            )
                    
                except StarfishError as e:
                    if ("not found" in str(e).lower() or "404" in str(e) or 
                        "400" in str(e) or "not finished yet" in str(e).lower()):
                        # Query still processing (400 = not finished yet, 404 = not found)
                        logger.debug("Query still processing", query_id=query_id, attempt=attempt+1, error=str(e))
                        continue
                    raise
            
            raise StarfishError(
                code="ASYNC_QUERY_TIMEOUT",
                message=f"Async query timed out after {timeout} seconds",
                details={"query_id": query_id, "max_attempts": max_attempts}
            )
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error("Async query execution failed", error=str(e))
            raise StarfishError(
                code="ASYNC_QUERY_FAILED",
                message="Async query execution failed",
                details={"error": str(e)}
            )

    async def query(self, query: str, format_fields: str = None, 
                   limit: int = 1000, sort_by: str = None, 
                   volumes_and_paths: str = None) -> List[StarfishEntry]:
        """Execute query against Starfish API."""
        params = {"query": query}
        
        if format_fields:
            params["format"] = format_fields
        else:
            # Default format with all useful fields
            params["format"] = "parent_path fn type size ct mt at uid gid mode volume tags_explicit tags_inherited"
        
        if limit:
            params["limit"] = str(limit)
        
        if sort_by:
            params["sort_by"] = sort_by
        
        if volumes_and_paths:
            params["volumes_and_paths"] = volumes_and_paths
        
        logger.info(
            "Executing Starfish query",
            query=query,
            limit=limit,
            format_fields=format_fields
        )
        
        try:
            # The Starfish API returns an array of entries directly
            entries_data = await self._request("GET", "/query/", params=params)
            
            if not isinstance(entries_data, list):
                raise StarfishError(
                    code="UNEXPECTED_RESPONSE_FORMAT",
                    message="Expected array of entries from query API"
                )
            
            entries = [StarfishEntry(**entry_data) for entry_data in entries_data]
            
            logger.info(
                "Query completed successfully",
                total_entries=len(entries)
            )
            
            # StarfishQueryResponse is now a type alias for List[StarfishQueryResult]
            return entries
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Query execution failed",
                query=query,
                error=str(e)
            )
            raise StarfishError(
                code="QUERY_FAILED",
                message="Query execution failed",
                details={"error": str(e)}
            )

    async def list_volumes(self) -> List[VolumeInfo]:
        """List all available volumes."""
        logger.info("Listing Starfish volumes")
        
        try:
            volumes_data = await self._request("GET", "/volume/")
            
            if not isinstance(volumes_data, list):
                raise StarfishError(
                    code="UNEXPECTED_RESPONSE_FORMAT",
                    message="Expected array of volumes from volumes API"
                )
            
            volumes = [VolumeInfo(**volume_data) for volume_data in volumes_data]
            
            logger.info(
                "Volumes listed successfully",
                total_volumes=len(volumes)
            )
            
            return volumes
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to list volumes",
                error=str(e)
            )
            raise StarfishError(
                code="LIST_VOLUMES_FAILED",
                message="Failed to list volumes",
                details={"error": str(e)}
            )

    async def list_collections(self, force_refresh: bool = False) -> List[str]:
        """List available collections/tagsets."""
        logger.info("Listing collections", force_refresh=force_refresh)
        
        try:
            params = {}
            if force_refresh:
                params["force_refresh"] = "true"
            
            # Get tags and extract collection names
            tags_data = await self._request("GET", "/tag/", params=params)
            
            if not isinstance(tags_data, dict) or "tags" not in tags_data:
                raise StarfishError(
                    code="UNEXPECTED_RESPONSE_FORMAT",
                    message="Expected tags object from tags API"
                )
            
            tags_response = StarfishTagsResponse(**tags_data)
            
            # Extract unique collection names from tags
            collections = set()
            for tag in tags_response.tags:
                if ":" in tag and not tag.startswith(":"):
                    collection_name = tag.split(":", 1)[0]
                    collections.add(collection_name)
            
            collection_list = sorted(list(collections))
            
            logger.info(
                "Collections listed successfully",
                total_collections=len(collection_list)
            )
            
            return collection_list
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to list collections",
                error=str(e)
            )
            raise StarfishError(
                code="LIST_COLLECTIONS_FAILED",
                message="Failed to list collections",
                details={"error": str(e)}
            )

    async def list_tagsets(self) -> List[Dict[str, Any]]:
        """List all available tagsets."""
        logger.info("Listing tagsets")
        
        try:
            # Call /tagset/ endpoint without ID to get all tagsets
            tagsets_data = await self._request("GET", "/tagset/")
            
            logger.info(
                "Tagsets listed successfully",
                total_tagsets=len(tagsets_data) if isinstance(tagsets_data, list) else 0
            )
            
            return tagsets_data if isinstance(tagsets_data, list) else []
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to list tagsets",
                error=str(e)
            )
            raise StarfishError(
                code="LIST_TAGSETS_FAILED",
                message="Failed to list tagsets",
                details={"error": str(e)}
            )

    async def get_tagset(self, tagset_name: str, limit: int = 1000, 
                        with_private: bool = True) -> Dict[str, Any]:
        """Get tags from a specific tagset."""
        logger.info("Getting tagset", tagset_name=tagset_name, limit=limit)
        
        try:
            params = {"limit": str(limit)}
            if with_private:
                params["with_private"] = "true"
            
            # For default tagset, use special syntax
            if tagset_name == "" or tagset_name == "default":
                endpoint = "/tagset/:/"
            else:
                endpoint = f"/tagset/{tagset_name}/"
            
            tagset_data = await self._request("GET", endpoint, params=params)
            
            logger.info(
                "Tagset retrieved successfully",
                tagset_name=tagset_name,
                total_tags=len(tagset_data.get("tags", []))
            )
            
            return tagset_data
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to get tagset",
                tagset_name=tagset_name,
                error=str(e)
            )
            raise StarfishError(
                code="GET_TAGSET_FAILED",
                message="Failed to get tagset",
                details={"tagset_name": tagset_name, "error": str(e)}
            )

    async def get_zone(self, zone_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific zone by ID."""
        logger.info("Getting zone details", zone_id=zone_id)
        
        try:
            zone_data = await self._request("GET", f"/zone/{zone_id}/")
            
            logger.info(
                "Zone retrieved successfully",
                zone_id=zone_id,
                zone_name=zone_data.get("name")
            )
            
            return zone_data
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to get zone",
                zone_id=zone_id,
                error=str(e)
            )
            raise StarfishError(
                code="GET_ZONE_FAILED",
                message="Failed to get zone",
                details={"zone_id": zone_id, "error": str(e)}
            )

    async def get_volume(self, volume_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific volume by ID."""
        logger.info("Getting volume details", volume_id=volume_id)
        
        try:
            volume_data = await self._request("GET", f"/volume/{volume_id}/")
            
            logger.info(
                "Volume retrieved successfully",
                volume_id=volume_id,
                volume_name=volume_data.get("vol")
            )
            
            return volume_data
            
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to get volume",
                volume_id=volume_id,
                error=str(e)
            )
            raise StarfishError(
                code="GET_VOLUME_FAILED",
                message="Failed to get volume",
                details={"volume_id": volume_id, "error": str(e)}
            )

    async def list_zones(self) -> List[StarfishZoneDetails]:
        """List all available zones."""
        logger.info("Listing Starfish zones")
        try:
            zones_data = await self._request("GET", "/zone/")
            if not isinstance(zones_data, list):
                raise StarfishError(
                    code="UNEXPECTED_RESPONSE_FORMAT",
                    message="Expected array of zones from zones API"
                )
            zones = [StarfishZoneDetails(**zone_data) for zone_data in zones_data]
            logger.info(
                "Zones listed successfully",
                total_zones=len(zones)
            )
            return zones
        except StarfishError:
            raise
        except Exception as e:
            logger.error(
                "Failed to list zones",
                error=str(e)
            )
            raise StarfishError(
                code="LIST_ZONES_FAILED",
                message="Failed to list zones",
                details={"error": str(e)}
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
        await self.token_manager.close()
