import time


class LFUCache:

    def __init__(self, capacity=100):
        self.capacity = capacity
        self.store = {}
        self.frequency = {}
        self.evictions = 0

    def put(self, key, value, ttl=300):

        expire_at = time.time() + ttl

        # Existing key
        if key in self.store:
            self.store[key] = {
                "value": value,
                "expire_at": expire_at
            }

            self.frequency[key] += 1
            return

        # Cache full → evict least frequently used
        if len(self.store) >= self.capacity:

            least_used_key = min(
                self.frequency,
                key=self.frequency.get
            )

            del self.store[least_used_key]
            del self.frequency[least_used_key]
            self.evictions += 1

        self.store[key] = {
            "value": value,
            "expire_at": expire_at
        }

        self.frequency[key] = 1

    def get(self, key):

        item = self.store.get(key)

        if item is None:
            return None

        # TTL expiration
        if time.time() > item["expire_at"]:

            del self.store[key]
            del self.frequency[key]

            return None

        self.frequency[key] += 1

        return item["value"]

    def delete(self, key):

        if key in self.store:
            del self.store[key]

        if key in self.frequency:
            del self.frequency[key]

    def size(self):

        return len(self.store)
    def get_evictions(self):
        return self.evictions