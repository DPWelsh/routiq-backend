"""
Simple rate limiter for API protection
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter with sliding window"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):  # 100 requests per hour default
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        
    def is_allowed(self, identifier: str) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed for identifier
        Returns (allowed, rate_limit_info)
        """
        try:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            # Get request history for this identifier
            request_times = self.requests[identifier]
            
            # Remove old requests outside the window
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Check if under limit
            request_count = len(request_times)
            allowed = request_count < self.max_requests
            
            if allowed:
                # Add current request
                request_times.append(current_time)
                logger.debug(f"Rate limit ALLOW: {identifier} ({request_count + 1}/{self.max_requests})")
            else:
                logger.warning(f"Rate limit EXCEEDED: {identifier} ({request_count}/{self.max_requests})")
            
            # Calculate when limit resets
            reset_time = request_times[0] + self.window_seconds if request_times else current_time
            remaining = max(0, self.max_requests - request_count - (1 if allowed else 0))
            
            rate_limit_info = {
                "allowed": allowed,
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": max(0, reset_time - current_time) if not allowed else 0
            }
            
            return allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limiter error for {identifier}: {e}")
            # On error, allow the request
            return True, {"error": str(e), "allowed": True}
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        try:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            total_identifiers = len(self.requests)
            active_identifiers = 0
            total_requests_in_window = 0
            
            for identifier, request_times in self.requests.items():
                # Clean old requests
                while request_times and request_times[0] < window_start:
                    request_times.popleft()
                
                if request_times:
                    active_identifiers += 1
                    total_requests_in_window += len(request_times)
            
            return {
                "total_identifiers": total_identifiers,
                "active_identifiers": active_identifiers,
                "total_requests_in_window": total_requests_in_window,
                "window_seconds": self.window_seconds,
                "max_requests_per_window": self.max_requests
            }
            
        except Exception as e:
            logger.error(f"Rate limiter stats error: {e}")
            return {"error": str(e)}
    
    def clear_identifier(self, identifier: str) -> None:
        """Clear rate limit history for identifier"""
        try:
            if identifier in self.requests:
                del self.requests[identifier]
                logger.info(f"Rate limit cleared for: {identifier}")
        except Exception as e:
            logger.error(f"Rate limit clear error for {identifier}: {e}")
    
    def cleanup_old_entries(self) -> int:
        """Remove expired entries to save memory"""
        try:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            cleaned_count = 0
            
            # Identify identifiers with no recent requests
            empty_identifiers = []
            for identifier, request_times in self.requests.items():
                # Clean old requests
                while request_times and request_times[0] < window_start:
                    request_times.popleft()
                
                # If no requests in window, mark for removal
                if not request_times:
                    empty_identifiers.append(identifier)
            
            # Remove empty identifiers
            for identifier in empty_identifiers:
                del self.requests[identifier]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Rate limiter cleanup: removed {cleaned_count} inactive identifiers")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Rate limiter cleanup error: {e}")
            return 0

class MultiTierRateLimiter:
    """Multi-tier rate limiter with different limits for different endpoints/users"""
    
    def __init__(self):
        self.limiters = {
            # Admin endpoints - more restrictive
            "admin": RateLimiter(max_requests=50, window_seconds=3600),  # 50/hour
            
            # Sync operations - very restrictive
            "sync": RateLimiter(max_requests=10, window_seconds=3600),   # 10/hour
            
            # Regular API - moderate
            "api": RateLimiter(max_requests=1000, window_seconds=3600),  # 1000/hour
            
            # Public endpoints - restrictive
            "public": RateLimiter(max_requests=100, window_seconds=3600), # 100/hour
        }
    
    def check_limit(self, tier: str, identifier: str) -> Tuple[bool, Dict[str, any]]:
        """Check rate limit for specific tier and identifier"""
        try:
            if tier not in self.limiters:
                logger.warning(f"Unknown rate limit tier: {tier}, using 'api' tier")
                tier = "api"
            
            return self.limiters[tier].is_allowed(identifier)
            
        except Exception as e:
            logger.error(f"Multi-tier rate limit error for {tier}/{identifier}: {e}")
            return True, {"error": str(e), "allowed": True}
    
    def get_all_stats(self) -> Dict[str, any]:
        """Get statistics for all rate limit tiers"""
        try:
            stats = {}
            for tier, limiter in self.limiters.items():
                stats[tier] = limiter.get_stats()
            
            return {
                "rate_limiter_stats": stats,
                "total_tiers": len(self.limiters)
            }
            
        except Exception as e:
            logger.error(f"Multi-tier stats error: {e}")
            return {"error": str(e)}
    
    def cleanup_all(self) -> int:
        """Cleanup all rate limiters"""
        try:
            total_cleaned = 0
            for tier, limiter in self.limiters.items():
                cleaned = limiter.cleanup_old_entries()
                total_cleaned += cleaned
            
            return total_cleaned
            
        except Exception as e:
            logger.error(f"Multi-tier cleanup error: {e}")
            return 0

# Global rate limiter instance
rate_limiter = MultiTierRateLimiter()

def get_rate_limit_identifier(request) -> str:
    """Extract identifier from request for rate limiting"""
    try:
        # Try to get organization ID from headers first
        org_id = getattr(request, 'headers', {}).get('x-organization-id')
        if org_id:
            return f"org:{org_id}"
        
        # Fall back to IP address
        client_ip = getattr(request, 'client', {}).host if hasattr(request, 'client') else 'unknown'
        return f"ip:{client_ip}"
        
    except Exception as e:
        logger.error(f"Rate limit identifier extraction error: {e}")
        return "unknown" 