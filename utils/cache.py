import time
from typing import Any, Optional, Dict
from collections import OrderedDict
from config.app_config import app_config

class LRUCache:
    """
    Simple LRU Cache implementation for storing embeddings and other frequently accessed data
    """
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired
        """
        if key in self.cache:
            item = self.cache[key]
            # Check if item has expired
            if time.time() - item['timestamp'] < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return item['value']
            else:
                # Remove expired item
                del self.cache[key]

        return None

    def put(self, key: str, value: Any):
        """
        Add value to cache
        """
        # Remove oldest item if cache is full
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        # Move to end (most recently used)
        self.cache.move_to_end(key)

    def delete(self, key: str):
        """
        Remove item from cache
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """
        Clear all items from cache
        """
        self.cache.clear()

    def size(self) -> int:
        """
        Get current cache size
        """
        return len(self.cache)

# Global cache instance
if app_config.cache_enabled:
    embedding_cache = LRUCache(max_size=500, ttl=app_config.cache_ttl)  # Cache for embeddings
    response_cache = LRUCache(max_size=200, ttl=app_config.cache_ttl)   # Cache for responses
    search_cache = LRUCache(max_size=300, ttl=app_config.cache_ttl)     # Cache for search results
else:
    # Create no-op cache if caching is disabled
    class NoOpCache:
        def get(self, key): return None
        def put(self, key, value): pass
        def delete(self, key): pass
        def clear(self): pass
        def size(self): return 0

    embedding_cache = NoOpCache()
    response_cache = NoOpCache()
    search_cache = NoOpCache()

def get_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments
    """
    import hashlib
    import json

    # Create a string representation of all arguments
    cache_input = json.dumps((args, sorted(kwargs.items())), sort_keys=True)
    # Generate hash to create a consistent key
    return hashlib.md5(cache_input.encode()).hexdigest()