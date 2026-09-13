import threading
import time


class IdleEvictionManager:

    def __init__(
        self,
        delete_callback,
        idle_timeout=600,
        check_interval=60
    ):

        self.delete_callback = delete_callback

        self.idle_timeout = idle_timeout
        self.check_interval = check_interval

        self.entries = {}

        self.lock = threading.Lock()

        self.stop_event = threading.Event()

        self.thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )

        self.thread.start()

    def track(self, key):

        key = str(key)

        now = time.time()

        with self.lock:

            if key not in self.entries:

                self.entries[key] = {
                    "last_access": now,
                    "access_count": 1
                }

            else:

                self.entries[key]["last_access"] = now

                self.entries[key]["access_count"] += 1

    def remove(self, key):

        key = str(key)

        with self.lock:

            self.entries.pop(
                key,
                None
            )

    def get_idle_keys(self):

        now = time.time()

        idle_keys = []

        with self.lock:

            for key, info in self.entries.items():

                idle_time = (
                    now -
                    info["last_access"]
                )

                if idle_time >= self.idle_timeout:

                    idle_keys.append(key)

        return idle_keys

    def get_status(self):

        now = time.time()

        with self.lock:

            result = {}

            for key, info in self.entries.items():

                result[key] = {
                    "last_access": info[
                        "last_access"
                    ],
                    "access_count": info[
                        "access_count"
                    ],
                    "idle_seconds": (
                        now -
                        info["last_access"]
                    )
                }

            return result

    def cleanup(self):

        idle_keys = self.get_idle_keys()

        evicted = 0

        for key in idle_keys:

            try:

                self.delete_callback(
                    key
                )

                self.remove(
                    key
                )

                evicted += 1

            except Exception:

                continue

        return evicted

    def _cleanup_loop(self):

        while not self.stop_event.wait(
            self.check_interval
        ):

            self.cleanup()

    def stop(self):

        self.stop_event.set()

        if self.thread.is_alive():

            self.thread.join(
                timeout=2
            )