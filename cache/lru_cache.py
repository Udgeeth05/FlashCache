from collections import OrderedDict
import time


class LRUCache:

    def __init__(self, capacity=100):
        self.capacity = capacity
        self.store = OrderedDict()
        self.evictions = 0

    def put(self, key, value, ttl=300):

        expire_at = time.time() + ttl

        if key in self.store:
            del self.store[key]

        self.store[key] = {
            "value": value,
            "expire_at": expire_at
        }

        self.store.move_to_end(key)

        if len(self.store) > self.capacity:
            self.store.popitem(last=False)
            self.evictions += 1

    def get(self, key):

        item = self.store.get(key)

        if item is None:
            return None

        if time.time() > item["expire_at"]:
            del self.store[key]
            return None

        self.store.move_to_end(key)

        return item["value"]

    def delete(self, key):

        if key in self.store:
            del self.store[key]

    def size(self):

        return len(self.store)

    def get_evictions(self):
        return self.evictions
    