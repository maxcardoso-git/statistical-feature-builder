"""
Rate limiting middleware.
"""
from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
import asyncio
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, consider using Redis-based rate limiting.
    """

    def __init__(self, requests_per_minute: int = 500):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start background task to clean up old entries."""
        asyncio.create_task(self._cleanup_old_entries())

    async def _cleanup_old_entries(self):
        """Periodically clean up old request timestamps."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            try:
                now = datetime.utcnow()
                cutoff = now - timedelta(minutes=1)

                for key in list(self.requests.keys()):
                    self.requests[key] = [
                        ts for ts in self.requests[key]
                        if ts > cutoff
                    ]
                    if not self.requests[key]:
                        del self.requests[key]

                logger.debug(f"Cleaned up rate limiter. Active keys: {len(self.requests)}")
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup: {e}")

    def _get_client_key(self, request: Request) -> str:
        """
        Generate a unique key for the client.

        Args:
            request: FastAPI request

        Returns:
            Client identifier key
        """
        # Try to get user from token
        user = getattr(request.state, "user", None)
        if user:
            return f"user:{user.get('sub', 'unknown')}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def check_rate_limit(self, request: Request) -> bool:
        """
        Check if request is within rate limit.

        Args:
            request: FastAPI request

        Returns:
            True if within limit

        Raises:
            HTTPException: If rate limit exceeded
        """
        if not settings.rate_limit_enabled:
            return True

        client_key = self._get_client_key(request)
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Get requests in the last minute
        recent_requests = [
            ts for ts in self.requests[client_key]
            if ts > minute_ago
        ]

        if len(recent_requests) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for {client_key}. "
                f"Requests: {len(recent_requests)}/{self.requests_per_minute}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "E006",
                    "message": "Rate limit exceeded",
                    "limit": self.requests_per_minute,
                    "window": "1 minute",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add current request
        self.requests[client_key].append(now)

        return True


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_requests_per_minute)
