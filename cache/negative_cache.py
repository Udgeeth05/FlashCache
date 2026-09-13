import threading
import time


class NegativeCache:

    def __init__(
        self,
        ttl=30,
        capacity=10000
    ):

        self.ttl = ttl
        self.capacity = capacity

        self.entries = {}

        self.lock = threading.Lock()

    def add(self, key):

        key = str(key)

        with self.lock:

            if len(self.entries) >= self.capacity:

                oldest_key = min(
                    self.entries,
                    key=self.entries.get
                )

                self.entries.pop(
                    oldest_key,
                    None
                )

            self.entries[key] = (
                time.time() + self.ttl
            )

    def contains(self, key):

        key = str(key)

        now = time.time()

        with self.lock:

            expiration = self.entries.get(
                key
            )

            if expiration is None:
                return False

            if now >= expiration:

                self.entries.pop(
                    key,
                    None
                )

                return False

            return True

    def remove(self, key):

        key = str(key)

        with self.lock:

            self.entries.pop(
                key,
                None
            )

    def cleanup(self):

        now = time.time()

        removed = 0

        with self.lock:

            expired = [
                key
                for key, expiration
                in self.entries.items()
                if now >= expiration
            ]

            for key in expired:

                self.entries.pop(
                    key,
                    None
                )

                removed += 1

        return removed

    def size(self):

        with self.lock:

            return len(
                self.entries
            )