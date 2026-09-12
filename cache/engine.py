import json
import time

from cache.lru_cache import LRUCache
from cache.lfu_cache import LFUCache
from cache.arc_cache import ARCCache
from cache.bloom_filter import BloomFilter


class CacheEngine:

    def __init__(self, capacity=100, policy="LRU"):

        self.policy = policy.upper()

        self.bloom_filter = BloomFilter(
            size=10000,
            hash_count=5
        )

        if self.policy == "LRU":
            self.cache = LRUCache(
                capacity=capacity
            )

        elif self.policy == "LFU":
            self.cache = LFUCache(
                capacity=capacity
            )

        elif self.policy == "ARC":
            self.cache = ARCCache(
                capacity=capacity
            )

        else:
            raise ValueError(
                f"Unsupported cache policy: {self.policy}"
            )

    def get(self, key):

        if not self.bloom_filter.might_contain(key):
            return None

        return self.cache.get(key)

    def put(self, key, value, ttl=300):

        payload = json.dumps(
            value,
            default=str
        ).encode("utf-8")

        if len(payload) > 5 * 1024 * 1024:
            raise ValueError(
                "Cache payload exceeds 5 MB limit"
            )

        self.bloom_filter.add(key)

        self.cache.put(
            key,
            value,
            ttl
        )

    def delete(self, key):

        self.cache.delete(key)

    def size(self):

        return self.cache.size()

    def get_evictions(self):

        return self.cache.get_evictions()