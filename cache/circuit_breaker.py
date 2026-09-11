import time
import threading


class CircuitBreaker:

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=3, recovery_timeout=10):

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED

        self.lock = threading.Lock()

    def allow_request(self):

        with self.lock:

            if self.state == self.CLOSED:
                return True

            if self.state == self.OPEN:

                if (
                    self.last_failure_time is not None
                    and time.time() - self.last_failure_time
                    >= self.recovery_timeout
                ):
                    self.state = self.HALF_OPEN
                    return True

                return False

            if self.state == self.HALF_OPEN:
                return True

            return False

    def record_success(self):

        with self.lock:

            self.failure_count = 0
            self.last_failure_time = None
            self.state = self.CLOSED

    def record_failure(self):

        with self.lock:

            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN

    def get_state(self):

        with self.lock:
            return self.state