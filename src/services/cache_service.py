"""
Simple in-memory cache service for performance optimization
"""

import time
import logging
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SimpleCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self, default_ttl_seconds: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        try:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() < entry['expires_at']:
                    logger.debug(f"Cache HIT: {key}")
                    return entry['value']
                else:
                    # Expired, remove entry
                    del self.cache[key]
                    logger.debug(f"Cache EXPIRED: {key}")
            
            logger.debug(f"Cache MISS: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            expires_at = time.time() + ttl
            
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items() 
                if current_time >= entry['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            current_time = time.time()
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values() 
                if current_time >= entry['expires_at']
            )
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "cache_size_bytes": len(str(self.cache))
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}

class CachedApiService:
    """Wrapper for API services with caching support"""
    
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache = SimpleCache(cache_ttl_seconds)
    
    def cached_call(self, cache_key: str, func: Callable, *args, ttl_seconds: Optional[int] = None, **kwargs) -> Any:
        """Execute function with caching"""
        try:
            # Try to get from cache first
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Cache miss - execute function
            logger.debug(f"Executing function for cache key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            self.cache.set(cache_key, result, ttl_seconds)
            
            return result
            
        except Exception as e:
            logger.error(f"Cached call error for key {cache_key}: {e}")
            # If caching fails, still try to execute the function
            return func(*args, **kwargs)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        try:
            matching_keys = [
                key for key in self.cache.cache.keys() 
                if pattern in key
            ]
            
            for key in matching_keys:
                self.cache.delete(key)
            
            logger.info(f"Invalidated {len(matching_keys)} cache entries matching pattern: {pattern}")
            return len(matching_keys)
            
        except Exception as e:
            logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
            return 0

# Global cache instances
# Organization data cache (longer TTL since it changes less frequently)
org_cache = CachedApiService(cache_ttl_seconds=900)  # 15 minutes

# API response cache (shorter TTL for fresher data)
api_cache = CachedApiService(cache_ttl_seconds=300)  # 5 minutes

# Database query cache (medium TTL)
db_cache = CachedApiService(cache_ttl_seconds=600)  # 10 minutes 