import threading
from collections import deque

from prometheus_client import (
    Counter,
    Gauge,
    Histogram
)


class CacheMetrics:

    def __init__(self):

        self.lock = threading.Lock()

        self.latencies = deque(
            maxlen=10000
        )

        self.requests = Counter(
            "flashcache_requests_total",
            "Total number of cache requests"
        )

        self.hits = Counter(
            "flashcache_hits_total",
            "Total number of cache hits"
        )

        self.misses = Counter(
            "flashcache_misses_total",
            "Total number of cache misses"
        )

        self.errors = Counter(
            "flashcache_errors_total",
            "Total number of cache errors"
        )

        self.evictions = Counter(
            "flashcache_evictions_total",
            "Total number of cache evictions"
        )

        self.cache_size = Gauge(
            "flashcache_cache_size",
            "Current number of cached entries"
        )

        self.memory_bytes = Gauge(
            "flashcache_memory_bytes",
            "Approximate cache memory usage in bytes"
        )

        self.hit_ratio = Gauge(
            "flashcache_hit_ratio",
            "Current cache hit ratio"
        )

        self.p99_latency = Gauge(
            "flashcache_p99_latency_ms",
            "Approximate P99 request latency in milliseconds"
        )

        self.request_latency = Histogram(
            "flashcache_request_latency_seconds",
            "Cache request latency in seconds",
            buckets=(
                0.0005,
                0.001,
                0.0025,
                0.005,
                0.01,
                0.025,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0
            )
        )

    def record_request(self, latency):

        self.requests.inc()

        self.request_latency.observe(
            latency
        )

        with self.lock:

            self.latencies.append(
                latency
            )

            self._update_p99()

        self._update_hit_ratio()

    def record_hit(self, latency):

        self.hits.inc()

        self.record_request(
            latency
        )

    def record_miss(self, latency):

        self.misses.inc()

        self.record_request(
            latency
        )

    def record_error(self):

        self.errors.inc()

    def record_eviction(self, count=1):

        self.evictions.inc(
            count
        )

    def update_cache_size(self, size):

        self.cache_size.set(
            size
        )

    def update_memory_bytes(self, size):

        self.memory_bytes.set(
            size
        )

    def _update_hit_ratio(self):

        total = (
            self.hits._value.get()
            +
            self.misses._value.get()
        )

        if total == 0:

            self.hit_ratio.set(0)

            return

        self.hit_ratio.set(
            self.hits._value.get() / total
        )

    def _update_p99(self):

        if not self.latencies:

            self.p99_latency.set(0)

            return

        values = sorted(
            self.latencies
        )

        index = int(
            len(values) * 0.99
        )

        if index >= len(values):

            index = len(values) - 1

        self.p99_latency.set(
            values[index] * 1000
        )

    def get_stats(self):

        total = (
            self.hits._value.get()
            +
            self.misses._value.get()
        )

        ratio = (
            self.hits._value.get() / total
            if total > 0
            else 0
        )

        with self.lock:

            values = list(
                self.latencies
            )

        if values:

            values.sort()

            index = int(
                len(values) * 0.99
            )

            if index >= len(values):

                index = len(values) - 1

            p99 = (
                values[index] * 1000
            )

        else:

            p99 = 0

        return {
            "requests": int(
                self.requests._value.get()
            ),
            "hits": int(
                self.hits._value.get()
            ),
            "misses": int(
                self.misses._value.get()
            ),
            "errors": int(
                self.errors._value.get()
            ),
            "evictions": int(
                self.evictions._value.get()
            ),
            "hit_ratio": ratio,
            "p99_latency_ms": p99
        }


# ONE shared metrics instance for the entire application.
metrics = CacheMetrics()