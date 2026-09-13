import math
import threading
import time


class PredictiveWarmer:

    def __init__(
        self,
        max_keys=10,
        decay_rate=0.01
    ):

        self.max_keys = max_keys

        self.decay_rate = decay_rate

        self.accesses = {}

        self.lock = threading.Lock()

    def record_access(self, key):

        key = str(key)

        now = time.time()

        with self.lock:

            if key not in self.accesses:

                self.accesses[key] = {
                    "count": 0,
                    "last_access": now
                }

            self.accesses[key]["count"] += 1

            self.accesses[key]["last_access"] = now

    def _calculate_score(self, info):

        age = (
            time.time()
            - info["last_access"]
        )

        decay = math.exp(
            -self.decay_rate * age
        )

        return (
            info["count"]
            * decay
        )

    def get_hot_keys(self):

        with self.lock:

            scored = []

            for key, info in self.accesses.items():

                score = self._calculate_score(
                    info
                )

                scored.append(
                    (
                        key,
                        score
                    )
                )

            scored.sort(
                key=lambda item: item[1],
                reverse=True
            )

            return [
                key
                for key, score in scored[
                    :self.max_keys
                ]
            ]

    def get_scores(self):

        with self.lock:

            scores = {}

            for key, info in self.accesses.items():

                scores[key] = self._calculate_score(
                    info
                )

            return scores

    def get_access_counts(self):

        with self.lock:

            return {
                key: info["count"]
                for key, info in self.accesses.items()
            }

    def get_last_access_times(self):

        with self.lock:

            return {
                key: info["last_access"]
                for key, info in self.accesses.items()
            }

    def remove(self, key):

        key = str(key)

        with self.lock:

            self.accesses.pop(
                key,
                None
            )

    def clear(self):

        with self.lock:

            self.accesses.clear()

    def size(self):

        with self.lock:

            return len(
                self.accesses
            )