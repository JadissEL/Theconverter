"""
Rate limiting middleware for API protection
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    requests_per_day: int = 1000
    burst_size: int = 5


class RateLimiter:
    """
    Token bucket rate limiter with multiple time windows
    Prevents API abuse and ensures fair usage
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        
        # Storage for rate limit tracking
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.day_requests: Dict[str, list] = defaultdict(list)
        
        # Token bucket for burst handling
        self.tokens: Dict[str, float] = defaultdict(lambda: self.config.burst_size)
        self.last_update: Dict[str, float] = defaultdict(time.time)
        
        # Cleanup task
        self._cleanup_task = None
    
    def _cleanup_old_requests(self, client_id: str):
        """Remove old request timestamps"""
        now = time.time()
        
        # Cleanup minute window (keep last 60 seconds)
        self.minute_requests[client_id] = [
            ts for ts in self.minute_requests[client_id]
            if now - ts < 60
        ]
        
        # Cleanup hour window (keep last 3600 seconds)
        self.hour_requests[client_id] = [
            ts for ts in self.hour_requests[client_id]
            if now - ts < 3600
        ]
        
        # Cleanup day window (keep last 86400 seconds)
        self.day_requests[client_id] = [
            ts for ts in self.day_requests[client_id]
            if now - ts < 86400
        ]
    
    def _refill_tokens(self, client_id: str):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_update[client_id]
        
        # Refill rate: 1 token per 6 seconds (10 per minute)
        refill_rate = self.config.requests_per_minute / 60.0
        tokens_to_add = elapsed * refill_rate
        
        self.tokens[client_id] = min(
            self.config.burst_size,
            self.tokens[client_id] + tokens_to_add
        )
        self.last_update[client_id] = now
    
    async def check_rate_limit(self, client_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed under rate limits
        
        Args:
            client_id: Unique identifier for client (IP, user ID, etc.)
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = time.time()
        
        # Cleanup old requests
        self._cleanup_old_requests(client_id)
        
        # Refill tokens
        self._refill_tokens(client_id)
        
        # Check token bucket (burst protection)
        if self.tokens[client_id] < 1:
            wait_time = (1 - self.tokens[client_id]) / (self.config.requests_per_minute / 60.0)
            return False, f"Rate limit exceeded. Try again in {int(wait_time)} seconds"
        
        # Check minute window
        minute_count = len(self.minute_requests[client_id])
        if minute_count >= self.config.requests_per_minute:
            return False, f"Rate limit: {self.config.requests_per_minute} requests per minute exceeded"
        
        # Check hour window
        hour_count = len(self.hour_requests[client_id])
        if hour_count >= self.config.requests_per_hour:
            return False, f"Rate limit: {self.config.requests_per_hour} requests per hour exceeded"
        
        # Check day window
        day_count = len(self.day_requests[client_id])
        if day_count >= self.config.requests_per_day:
            return False, f"Rate limit: {self.config.requests_per_day} requests per day exceeded"
        
        # Request is allowed - record it
        self.minute_requests[client_id].append(now)
        self.hour_requests[client_id].append(now)
        self.day_requests[client_id].append(now)
        
        # Consume token
        self.tokens[client_id] -= 1
        
        return True, None
    
    def get_remaining(self, client_id: str) -> Dict[str, int]:
        """
        Get remaining requests for each time window
        
        Args:
            client_id: Client identifier
        
        Returns:
            Dictionary with remaining requests
        """
        self._cleanup_old_requests(client_id)
        
        return {
            'minute': self.config.requests_per_minute - len(self.minute_requests[client_id]),
            'hour': self.config.requests_per_hour - len(self.hour_requests[client_id]),
            'day': self.config.requests_per_day - len(self.day_requests[client_id]),
            'tokens': int(self.tokens[client_id])
        }
    
    def reset(self, client_id: str):
        """Reset rate limits for a client"""
        self.minute_requests[client_id].clear()
        self.hour_requests[client_id].clear()
        self.day_requests[client_id].clear()
        self.tokens[client_id] = self.config.burst_size
        self.last_update[client_id] = time.time()
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Cleanup all clients
            for client_id in list(self.minute_requests.keys()):
                self._cleanup_old_requests(client_id)
                
                # Remove completely empty clients
                if (not self.minute_requests[client_id] and
                    not self.hour_requests[client_id] and
                    not self.day_requests[client_id]):
                    
                    del self.minute_requests[client_id]
                    del self.hour_requests[client_id]
                    del self.day_requests[client_id]
                    del self.tokens[client_id]
                    del self.last_update[client_id]
