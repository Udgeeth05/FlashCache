import time


class CacheMetrics:

    def __init__(self):
        self.total_requests = 0
        self.hits = 0
        self.misses = 0
        self.total_latency = 0.0

    def record_hit(self, latency):
        self.total_requests += 1
        self.hits += 1
        self.total_latency += latency

    def record_miss(self, latency):
        self.total_requests += 1
        self.misses += 1
        self.total_latency += latency

    def get_stats(self):

        if self.total_requests == 0:
            hit_rate = 0
            miss_rate = 0
            average_latency = 0

        else:
            hit_rate = (self.hits / self.total_requests) * 100
            miss_rate = (self.misses / self.total_requests) * 100
            average_latency = (
                self.total_latency / self.total_requests
            )

        return {
            "total_requests": self.total_requests,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "miss_rate_percent": round(miss_rate, 2),
            "average_latency_ms": round(
                average_latency * 1000, 2
            )
        }