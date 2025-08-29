"""Tests for the RateLimiter class."""

import pytest
import asyncio
import time
from starfish_mcp.rate_limiter import RateLimiter


def test_rate_limiter_basic_functionality():
    """Test basic rate limiter functionality."""
    limiter = RateLimiter(max_queries=2, time_window_seconds=1, enabled=True)
    
    # First 2 queries should be allowed
    allowed, error = limiter.check_rate_limit()
    assert allowed is True
    assert error is None
    
    allowed, error = limiter.check_rate_limit()
    assert allowed is True
    assert error is None
    
    # Third query should be blocked
    allowed, error = limiter.check_rate_limit()
    assert allowed is False
    assert "RATE LIMIT EXCEEDED" in error
    assert "2/2 queries in 1 seconds" in error


def test_rate_limiter_disabled():
    """Test rate limiter when disabled."""
    limiter = RateLimiter(max_queries=1, time_window_seconds=1, enabled=False)
    
    # Should allow unlimited queries when disabled
    for _ in range(10):
        allowed, error = limiter.check_rate_limit()
        assert allowed is True
        assert error is None


def test_rate_limiter_time_window():
    """Test that rate limiter respects time windows."""
    limiter = RateLimiter(max_queries=2, time_window_seconds=0.1, enabled=True)
    
    # Use up quota
    limiter.check_rate_limit()
    limiter.check_rate_limit()
    
    # Should be blocked
    allowed, error = limiter.check_rate_limit()
    assert allowed is False
    
    # Wait for window to expire
    time.sleep(0.15)
    
    # Should be allowed again
    allowed, error = limiter.check_rate_limit()
    assert allowed is True


def test_rate_limiter_status():
    """Test rate limiter status reporting."""
    limiter = RateLimiter(max_queries=3, time_window_seconds=10, enabled=True)
    
    # Initial status
    status = limiter.get_status()
    assert status["enabled"] is True
    assert status["current_queries"] == 0
    assert status["max_queries"] == 3
    assert status["queries_remaining"] == 3
    assert status["time_window_seconds"] == 10
    
    # After one query
    limiter.check_rate_limit()
    status = limiter.get_status()
    assert status["current_queries"] == 1
    assert status["queries_remaining"] == 2
    
    # After hitting limit
    limiter.check_rate_limit()
    limiter.check_rate_limit()
    status = limiter.get_status()
    assert status["current_queries"] == 3
    assert status["queries_remaining"] == 0


def test_rate_limiter_reset():
    """Test rate limiter reset functionality."""
    limiter = RateLimiter(max_queries=2, time_window_seconds=10, enabled=True)
    
    # Use up quota
    limiter.check_rate_limit()
    limiter.check_rate_limit()
    
    status = limiter.get_status()
    assert status["current_queries"] == 2
    
    # Reset
    limiter.reset()
    
    status = limiter.get_status()
    assert status["current_queries"] == 0
    assert status["queries_remaining"] == 2
    
    # Should be able to query again
    allowed, error = limiter.check_rate_limit()
    assert allowed is True


def test_rate_limiter_config_update():
    """Test updating rate limiter configuration."""
    limiter = RateLimiter(max_queries=5, time_window_seconds=10, enabled=True)
    
    # Update configuration
    limiter.update_config(max_queries=3, time_window_seconds=5, enabled=False)
    
    assert limiter.max_queries == 3
    assert limiter.time_window_seconds == 5
    assert limiter.enabled is False
    
    # Test partial updates
    limiter.update_config(enabled=True)
    assert limiter.enabled is True
    assert limiter.max_queries == 3  # Should remain unchanged


def test_rate_limiter_status_disabled():
    """Test status when rate limiting is disabled."""
    limiter = RateLimiter(max_queries=5, time_window_seconds=10, enabled=False)
    
    # Make some queries (should all be allowed)
    for _ in range(10):
        limiter.check_rate_limit()
    
    status = limiter.get_status()
    assert status["enabled"] is False
    assert status["current_queries"] == 0  # Should always be 0 when disabled
    assert status["max_queries"] == 5  # Max queries value
    assert status["time_to_reset"] == 0


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window():
    """Test sliding window behavior with real timing."""
    limiter = RateLimiter(max_queries=2, time_window_seconds=0.2, enabled=True)
    
    # Fill up the window
    start_time = time.time()
    limiter.check_rate_limit()  # Query 1
    await asyncio.sleep(0.1)    # Wait 0.1 seconds
    limiter.check_rate_limit()  # Query 2
    
    # Should be blocked now
    allowed, error = limiter.check_rate_limit()
    assert allowed is False
    
    # Wait for first query to expire (total 0.2+ seconds)
    await asyncio.sleep(0.15)  # Total time: 0.25 seconds
    
    # Now should be allowed (first query expired)
    allowed, error = limiter.check_rate_limit()
    assert allowed is True
    
    elapsed = time.time() - start_time
    assert elapsed >= 0.2  # Verify we waited long enough


def test_rate_limiter_error_messages():
    """Test that error messages contain useful information."""
    limiter = RateLimiter(max_queries=2, time_window_seconds=5, enabled=True)
    
    # Fill quota
    limiter.check_rate_limit()
    limiter.check_rate_limit()
    
    # Get error message
    allowed, error = limiter.check_rate_limit()
    assert allowed is False
    assert "🚨 RATE LIMIT EXCEEDED" in error
    assert "2/2 queries in 5 seconds" in error
    assert "Please wait" in error
    assert "seconds before trying again" in error
    assert "use broader queries" in error


def test_rate_limiter_with_zero_queries():
    """Test edge case with zero query limit."""
    limiter = RateLimiter(max_queries=0, time_window_seconds=10, enabled=True)
    
    # Should immediately block
    allowed, error = limiter.check_rate_limit()
    assert allowed is False
    assert "0/0 queries" in error


def test_rate_limiter_wait_time_accuracy():
    """Test that wait time calculation is reasonably accurate."""
    limiter = RateLimiter(max_queries=1, time_window_seconds=2, enabled=True)
    
    start_time = time.time()
    limiter.check_rate_limit()  # Use quota
    
    # Check wait time immediately
    allowed, error = limiter.check_rate_limit()
    assert allowed is False
    
    status = limiter.get_status()
    wait_time = status["time_to_reset"]
    
    # Wait time should be close to 2 seconds (within 0.1s tolerance)
    assert 1.9 <= wait_time <= 2.1
    
    # Wait time should decrease over time
    time.sleep(0.1)
    status = limiter.get_status()
    new_wait_time = status["time_to_reset"]
    assert new_wait_time < wait_time
