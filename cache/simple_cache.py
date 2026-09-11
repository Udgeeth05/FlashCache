import time

class SimpleCache:
    def __init__(self):
        self.store = {}  # this dict holds our data

    def put(self, key, value, ttl=300):
        expire_at = time.time() + ttl
        self.store[key] = {"value": value, "expire_at": expire_at}

    def get(self, key):
        item = self.store.get(key)
        if item is None:
            return None
        if time.time() > item["expire_at"]:
            del self.store[key]
            return None
        return item["value"]

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            