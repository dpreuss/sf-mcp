#!/usr/bin/env python3
"""Demo script showing the new rate limiting functionality."""

import asyncio
import time
from starfish_mcp.rate_limiter import RateLimiter


async def demo_rate_limiting():
    """Demonstrate rate limiting functionality."""
    print("🚨 Rate Limiting Demo")
    print("=" * 50)
    
    # Create a rate limiter: 3 queries per 5 seconds
    limiter = RateLimiter(max_queries=3, time_window_seconds=5, enabled=True)
    
    print(f"Rate Limiter: {limiter.max_queries} queries per {limiter.time_window_seconds} seconds")
    print()
    
    # Try to make 6 queries quickly
    for i in range(6):
        allowed, error_msg = limiter.check_rate_limit()
        status = limiter.get_status()
        
        print(f"Query {i+1}:")
        print(f"  Allowed: {allowed}")
        print(f"  Current queries: {status['current_queries']}/{status['max_queries']}")
        print(f"  Remaining: {status['queries_remaining']}")
        
        if not allowed:
            print(f"  ❌ Blocked: {error_msg}")
            print(f"  ⏳ Wait time: {status['time_to_reset']:.1f} seconds")
        else:
            print(f"  ✅ Query executed")
        
        print()
        
        # Small delay between queries
        await asyncio.sleep(0.5)
    
    print("⏰ Waiting for rate limit to reset...")
    await asyncio.sleep(6)  # Wait for window to clear
    
    print("\n🔄 After waiting:")
    status = limiter.get_status()
    print(f"  Current queries: {status['current_queries']}/{status['max_queries']}")
    print(f"  Remaining: {status['queries_remaining']}")
    
    # Try one more query
    allowed, _ = limiter.check_rate_limit()
    print(f"  New query allowed: {allowed} ✅")
    
    print("\n🔧 Testing manual reset:")
    limiter.check_rate_limit()  # Use one more
    limiter.check_rate_limit()  # Use another
    
    print("Before reset:", limiter.get_status()['current_queries'])
    limiter.reset()
    print("After reset:", limiter.get_status()['current_queries'])
    
    print("\n✨ Rate limiting demo complete!")


async def demo_disabled_rate_limiting():
    """Demo with rate limiting disabled."""
    print("\n🚫 Disabled Rate Limiting Demo")
    print("=" * 50)
    
    limiter = RateLimiter(max_queries=1, time_window_seconds=1, enabled=False)
    print("Rate limiting disabled - should allow unlimited queries")
    
    for i in range(5):
        allowed, _ = limiter.check_rate_limit()
        print(f"Query {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")
    
    status = limiter.get_status()
    print(f"\nStatus: {status}")


if __name__ == "__main__":
    asyncio.run(demo_rate_limiting())
    asyncio.run(demo_disabled_rate_limiting())
