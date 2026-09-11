from cache.lru_cache import LRUCache
from cache.lfu_cache import LFUCache
from cache.arc_cache import ARCCache
from cache.bloom_filter import BloomFilter

import time

from cache.metrics import (
    cache_requests,
    cache_hits,
    cache_misses,
    cache_size,
    cache_evictions,
    cache_latency,
)

class CacheEngine:

    def __init__(self, capacity=100, policy="LRU"):

        self.policy = policy.upper()

        # Bloom Filter for fast cache-key existence checks
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
        start_time = time.perf_counter()

        cache_requests.inc()

        # Bloom Filter check
        if not self.bloom_filter.might_contain(key):

            cache_misses.inc()

            cache_latency.observe(
                time.perf_counter() - start_time
            )

            return None

        value = self.cache.get(key)

        if value is None:
            cache_misses.inc()
        else:
            cache_hits.inc()

        cache_latency.observe(
            time.perf_counter() - start_time
        )

        return value

    def put(self, key, value, ttl=300):
        self.bloom_filter.add(key)

        self.cache.put(
            key,
            value,
            ttl
        )

        cache_size.set(
            self.cache.size()
        )

    def delete(self, key):
        self.cache.delete(key)

        cache_size.set(
            self.cache.size()
        )

    def size(self):

        return self.cache.size()

    def get_evictions(self):

        return self.cache.get_evictions()