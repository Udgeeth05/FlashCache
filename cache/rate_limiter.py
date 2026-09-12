import time
import threading


class TokenBucket:

    def __init__(
        self,
        capacity=10,
        refill_rate=5
    ):

        self.capacity = capacity
        self.refill_rate = refill_rate

        self.tokens = {}
        self.lock = threading.Lock()

    def allow(self, client_id):

        now = time.time()

        with self.lock:

            if client_id not in self.tokens:

                self.tokens[client_id] = {
                    "tokens": float(self.capacity),
                    "last_update": now
                }

            bucket = self.tokens[client_id]

            elapsed = now - bucket["last_update"]

            bucket["tokens"] = min(
                self.capacity,
                bucket["tokens"] +
                elapsed * self.refill_rate
            )

            bucket["last_update"] = now

            if bucket["tokens"] >= 1:

                bucket["tokens"] -= 1

                return True

            return False

    def reset(self, client_id):

        with self.lock:
            self.tokens.pop(client_id, None)