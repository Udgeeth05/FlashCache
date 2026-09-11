from prometheus_client import Counter, Gauge, Histogram


# Total requests received by FlashCache
cache_requests = Counter(
    "flashcache_requests_total",
    "Total number of cache requests"
)


# Cache hits
cache_hits = Counter(
    "flashcache_hits_total",
    "Total number of cache hits"
)


# Cache misses
cache_misses = Counter(
    "flashcache_misses_total",
    "Total number of cache misses"
)


# Number of items currently in cache
cache_size = Gauge(
    "flashcache_cache_size",
    "Current number of items in cache"
)


# Number of evictions
cache_evictions = Counter(
    "flashcache_evictions_total",
    "Total number of evicted cache entries"
)


# Cache request latency
cache_latency = Histogram(
    "flashcache_request_latency_seconds",
    "Cache request latency"
)