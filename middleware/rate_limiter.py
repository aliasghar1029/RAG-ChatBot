import time
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from config.app_config import app_config

class RateLimiter:
    def __init__(self):
        # Store request timestamps for each identifier
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.window_size = app_config.rate_limit_window  # in seconds
        self.max_requests = app_config.rate_limit_requests

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if a request from the given identifier is allowed
        """
        now = time.time()
        window_start = now - self.window_size

        # Remove outdated requests
        while self.requests[identifier] and self.requests[identifier][0] < window_start:
            self.requests[identifier].popleft()

        # Check if we're under the limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True

        return False

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request):
    """
    Middleware function to apply rate limiting
    """
    if not app_config.rate_limit_enabled:
        return

    # Identify the client (you could use IP address, user ID, API key, etc.)
    client_id = request.client.host  # Using IP address as identifier

    # Add additional identification if available (e.g., from headers)
    user_id = request.headers.get("user-id") or request.headers.get("x-user-id")
    if user_id:
        client_id = f"{client_id}:{user_id}"

    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": f"Rate limit exceeded. Maximum {app_config.rate_limit_requests} requests per {app_config.rate_limit_window} seconds."
            }
        )

# Decorator for applying rate limiting to specific routes
def with_rate_limit(func):
    """
    Decorator to add rate limiting to specific endpoints
    """
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request') or (args[0] if args and hasattr(args[0], 'client') else None)
        if request:
            await rate_limit_middleware(request)
        return await func(*args, **kwargs)
    return wrapper