"""
Smart caching layer for pipeline optimization
"""

import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class SmartCache:
    """
    Intelligent caching system for pipeline optimization
    
    Features:
    - URL content caching
    - Parsed event data caching  
    - TTL-based expiration
    - Memory usage limits
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl  # seconds
        
        # Cache stores: {key: {"data": ..., "timestamp": ..., "ttl": ...}}
        self.url_content_cache = {}
        self.parsed_events_cache = {}
        self.access_times = {}  # For LRU eviction
        
    def get_url_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached URL content if available and not expired"""
        cache_key = self._hash_key(url)
        return self._get_from_cache(self.url_content_cache, cache_key)
    
    def cache_url_content(self, url: str, content_data: Dict[str, Any], ttl: Optional[int] = None):
        """Cache URL content with optional custom TTL"""
        cache_key = self._hash_key(url)
        self._store_in_cache(self.url_content_cache, cache_key, content_data, ttl)
    
    def get_parsed_event(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached parsed event data"""
        return self._get_from_cache(self.parsed_events_cache, content_hash)
    
    def cache_parsed_event(self, content: str, parsed_data: Dict[str, Any], ttl: Optional[int] = None):
        """Cache parsed event data"""
        content_hash = self._hash_key(content)
        self._store_in_cache(self.parsed_events_cache, content_hash, parsed_data, ttl)
    
    def _hash_key(self, content: str) -> str:
        """Create hash key for content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, cache: Dict, key: str) -> Optional[Dict[str, Any]]:
        """Get item from cache if not expired"""
        if key not in cache:
            return None
            
        cached_item = cache[key]
        
        # Check if expired
        if self._is_expired(cached_item):
            del cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None
        
        # Update access time for LRU
        self.access_times[key] = time.time()
        return cached_item["data"]
    
    def _store_in_cache(self, cache: Dict, key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """Store item in cache with TTL"""
        # Enforce size limits
        if len(cache) >= self.max_size:
            self._evict_lru(cache)
        
        cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl or self.default_ttl
        }
        self.access_times[key] = time.time()
    
    def _is_expired(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is expired"""
        age = time.time() - cached_item["timestamp"]
        return age > cached_item["ttl"]
    
    def _evict_lru(self, cache: Dict):
        """Evict least recently used item"""
        if not self.access_times:
            return
            
        # Find least recently accessed key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove from both caches and access times
        cache.pop(lru_key, None)
        self.access_times.pop(lru_key, None)
    
    def cleanup_expired(self):
        """Remove all expired items from caches"""
        current_time = time.time()
        
        # Clean URL content cache
        expired_keys = []
        for key, item in self.url_content_cache.items():
            if current_time - item["timestamp"] > item["ttl"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.url_content_cache.pop(key, None)
            self.access_times.pop(key, None)
        
        # Clean parsed events cache
        expired_keys = []
        for key, item in self.parsed_events_cache.items():
            if current_time - item["timestamp"] > item["ttl"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.parsed_events_cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return {
            "url_content_cache_size": len(self.url_content_cache),
            "parsed_events_cache_size": len(self.parsed_events_cache),
            "total_cache_size": len(self.url_content_cache) + len(self.parsed_events_cache),
            "max_size": self.max_size,
            "cache_utilization": (len(self.url_content_cache) + len(self.parsed_events_cache)) / (self.max_size * 2) * 100,
            "default_ttl": self.default_ttl
        }
    
    def clear_all_caches(self):
        """Clear all cached data"""
        self.url_content_cache.clear()
        self.parsed_events_cache.clear()
        self.access_times.clear()