"""Rate limiting implementation for Starfish MCP server."""

import time
from collections import deque
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Time-based sliding window rate limiter."""
    
    def __init__(self, max_queries: int = 5, time_window_seconds: int = 10, enabled: bool = True):
        """Initialize rate limiter.
        
        Args:
            max_queries: Maximum number of queries allowed in the time window
            time_window_seconds: Time window in seconds for rate limiting
            enabled: Whether rate limiting is enabled
        """
        self.max_queries = max_queries
        self.time_window_seconds = time_window_seconds
        self.enabled = enabled
        self._query_timestamps = deque()
        
        logger.info(
            "Rate limiter initialized",
            max_queries=max_queries,
            time_window_seconds=time_window_seconds,
            enabled=enabled
        )
    
    def check_rate_limit(self) -> tuple[bool, Optional[str]]:
        """Check if a new query is allowed under the rate limit.
        
        Returns:
            Tuple of (allowed, error_message). If allowed is False, error_message 
            contains the reason for denial.
        """
        if not self.enabled:
            return True, None
            
        now = time.time()
        
        # Clean up old timestamps outside the time window
        while self._query_timestamps and now - self._query_timestamps[0] > self.time_window_seconds:
            self._query_timestamps.popleft()
        
        # Check if we're at the limit
        if len(self._query_timestamps) >= self.max_queries:
            oldest_query_time = self._query_timestamps[0]
            wait_time = self.time_window_seconds - (now - oldest_query_time)
            
            logger.warning(
                "Rate limit exceeded",
                current_queries=len(self._query_timestamps),
                max_queries=self.max_queries,
                time_window=self.time_window_seconds,
                wait_time_seconds=wait_time
            )
            
            error_msg = (
                f"🚨 RATE LIMIT EXCEEDED: {len(self._query_timestamps)}/{self.max_queries} queries "
                f"in {self.time_window_seconds} seconds. Please wait {wait_time:.1f} seconds before "
                f"trying again, or use broader queries to reduce API calls."
            )
            return False, error_msg
        
        # Record this query
        self._query_timestamps.append(now)
        
        logger.debug(
            "Query allowed",
            queries_in_window=len(self._query_timestamps),
            max_queries=self.max_queries,
            time_window=self.time_window_seconds
        )
        
        return True, None
    
    def reset(self):
        """Reset the rate limiter, clearing all recorded queries."""
        query_count = len(self._query_timestamps)
        self._query_timestamps.clear()
        
        logger.info(
            "Rate limiter reset",
            cleared_queries=query_count
        )
    
    def get_status(self) -> dict:
        """Get current rate limiter status.
        
        Returns:
            Dictionary with current status information
        """
        if not self.enabled:
            return {
                "enabled": False,
                "current_queries": 0,
                "max_queries": self.max_queries,
                "time_window_seconds": self.time_window_seconds,
                "time_to_reset": 0
            }
        
        now = time.time()
        
        # Clean up old timestamps
        while self._query_timestamps and now - self._query_timestamps[0] > self.time_window_seconds:
            self._query_timestamps.popleft()
        
        time_to_reset = 0
        if self._query_timestamps:
            oldest_query_time = self._query_timestamps[0]
            time_to_reset = max(0, self.time_window_seconds - (now - oldest_query_time))
        
        return {
            "enabled": self.enabled,
            "current_queries": len(self._query_timestamps),
            "max_queries": self.max_queries,
            "time_window_seconds": self.time_window_seconds,
            "time_to_reset": time_to_reset,
            "queries_remaining": max(0, self.max_queries - len(self._query_timestamps))
        }
    
    def update_config(self, max_queries: Optional[int] = None, 
                     time_window_seconds: Optional[int] = None,
                     enabled: Optional[bool] = None):
        """Update rate limiter configuration at runtime.
        
        Args:
            max_queries: New maximum query limit
            time_window_seconds: New time window
            enabled: New enabled state
        """
        old_config = {
            "max_queries": self.max_queries,
            "time_window_seconds": self.time_window_seconds,
            "enabled": self.enabled
        }
        
        if max_queries is not None:
            self.max_queries = max_queries
        if time_window_seconds is not None:
            self.time_window_seconds = time_window_seconds
        if enabled is not None:
            self.enabled = enabled
            
        logger.info(
            "Rate limiter configuration updated",
            old_config=old_config,
            new_config={
                "max_queries": self.max_queries,
                "time_window_seconds": self.time_window_seconds,
                "enabled": self.enabled
            }
        )
