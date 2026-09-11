from collections import OrderedDict
import time


class ARCCache:

    def __init__(self, capacity=100):

        self.capacity = capacity

        # Recently used resident entries
        self.t1 = OrderedDict()

        # Frequently used resident entries
        self.t2 = OrderedDict()

        # Recently evicted history
        self.b1 = OrderedDict()

        # Frequently evicted history
        self.b2 = OrderedDict()

        # Adaptive target size for T1
        self.p = 0
        self.evictions = 0

    def _remove_oldest(self, cache):

        if cache:
            return cache.popitem(last=False)

        return None

    def _trim_history(self):

        while len(self.b1) + len(self.b2) > self.capacity:

            if len(self.b1) > len(self.b2):
                self._remove_oldest(self.b1)

            else:
                self._remove_oldest(self.b2)

    def _evict(self):

        total_resident = len(self.t1) + len(self.t2)

        if total_resident < self.capacity:
            return

        # Prefer T1 when it exceeds adaptive target
        if len(self.t1) > self.p:

            key, item = self._remove_oldest(self.t1)

            self.b1[key] = time.time()
            self.evictions += 1

        elif self.t2:

            key, item = self._remove_oldest(self.t2)

            self.b2[key] = time.time()
            self.evictions += 1

        elif self.t1:

            key, item = self._remove_oldest(self.t1)

            self.b1[key] = time.time()
            self.evictions += 1

        self._trim_history()

    def put(self, key, value, ttl=300):

        expire_at = time.time() + ttl

        # Already in T1 → promote to T2
        if key in self.t1:

            del self.t1[key]

            self.t2[key] = {
                "value": value,
                "expire_at": expire_at
            }

            return

        # Already in T2 → refresh
        if key in self.t2:

            del self.t2[key]

            self.t2[key] = {
                "value": value,
                "expire_at": expire_at
            }

            return

        # Key was recently evicted from T1
        if key in self.b1:

            del self.b1[key]

            self.p = min(
                self.capacity,
                self.p + 1
            )

            self._evict()

            self.t2[key] = {
                "value": value,
                "expire_at": expire_at
            }

            return

        # Key was recently evicted from T2
        if key in self.b2:

            del self.b2[key]

            self.p = max(
                0,
                self.p - 1
            )

            self._evict()

            self.t2[key] = {
                "value": value,
                "expire_at": expire_at
            }

            return

        # New item
        self._evict()

        self.t1[key] = {
            "value": value,
            "expire_at": expire_at
        }

        self._trim_history()

    def get(self, key):

        # Check T1
        if key in self.t1:

            item = self.t1.pop(key)

            if time.time() > item["expire_at"]:
                return None

            # Promote to frequently used
            self.t2[key] = item

            return item["value"]

        # Check T2
        if key in self.t2:

            item = self.t2.pop(key)

            if time.time() > item["expire_at"]:

                return None

            self.t2[key] = item

            return item["value"]

        return None

    def delete(self, key):

        self.t1.pop(key, None)
        self.t2.pop(key, None)
        self.b1.pop(key, None)
        self.b2.pop(key, None)

    def size(self):

        return len(self.t1) + len(self.t2)
    def get_evictions(self):
        return self.evictions