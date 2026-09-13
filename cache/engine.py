import json
import sys

from cache.lru_cache import LRUCache
from cache.lfu_cache import LFUCache
from cache.arc_cache import ARCCache
from cache.bloom_filter import BloomFilter
from cache.persistence import CachePersistence


class CacheEngine:

    def __init__(
        self,
        capacity=100,
        policy="LRU",
        persistence=None
    ):

        self.capacity = capacity
        self.policy = policy.upper()
        self.persistence = persistence

        self.recovering = False

        self.bloom_filter = BloomFilter(
            size=10000,
            hash_count=5
        )

        self.entry_sizes = {}

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

        if self.persistence is not None:

            self._recover()

    def _recover(self):

        self.recovering = True

        try:

            records = self.persistence.load_aof()

            for record in records:

                operation = record.get(
                    "operation"
                )

                key = record.get(
                    "key"
                )

                value = record.get(
                    "value"
                )

                ttl = record.get(
                    "ttl",
                    300
                )

                if key is None:

                    continue

                key = str(key)

                if operation == "PUT":

                    if value is not None:

                        self.bloom_filter.add(
                            key
                        )

                        self.cache.put(
                            key,
                            value,
                            ttl
                        )

                        self.entry_sizes[key] = (
                            self._calculate_size(
                                value
                            )
                        )

                elif operation == "DELETE":

                    self.cache.delete(
                        key
                    )

                    self.entry_sizes.pop(
                        key,
                        None
                    )

        finally:

            self.recovering = False

    def _calculate_size(
        self,
        value
    ):

        try:

            return len(
                json.dumps(
                    value,
                    default=str
                ).encode("utf-8")
            )

        except Exception:

            return sys.getsizeof(
                value
            )

    def get(
        self,
        key
    ):

        key = str(key)

        if not self.bloom_filter.might_contain(
            key
        ):

            return None

        return self.cache.get(
            key
        )

    def put(
        self,
        key,
        value,
        ttl=300,
        fetch_time=0
    ):

        key = str(key)

        payload = json.dumps(
            value,
            default=str
        ).encode("utf-8")

        if len(payload) > 5 * 1024 * 1024:

            raise ValueError(
                "Cache payload exceeds 5 MB limit"
            )

        self.bloom_filter.add(
            key
        )

        self.entry_sizes[key] = len(
            payload
        )

        if self.policy == "LRU":

            self.cache.put(
                key,
                value,
                ttl,
                fetch_time
            )

        else:

            self.cache.put(
                key,
                value,
                ttl
            )

        if (
            self.persistence is not None
            and not self.recovering
        ):

            self.persistence.append(
                operation="PUT",
                key=key,
                value=value,
                ttl=ttl
            )

    def delete(
        self,
        key
    ):

        key = str(key)

        self.cache.delete(
            key
        )

        self.entry_sizes.pop(
            key,
            None
        )

        if (
            self.persistence is not None
            and not self.recovering
        ):

            self.persistence.append(
                operation="DELETE",
                key=key
            )

    def snapshot(self):

        if self.persistence is None:

            return False

        data = {}

        if hasattr(
            self.cache,
            "store"
        ):

            for key, item in self.cache.store.items():

                if isinstance(
                    item,
                    dict
                ):

                    data[key] = item

        self.persistence.snapshot(
            data
        )

        return True

    def size(self):

        return self.cache.size()

    def memory_bytes(self):

        return sum(
            self.entry_sizes.values()
        )

    def get_evictions(self):

        return self.cache.get_evictions()