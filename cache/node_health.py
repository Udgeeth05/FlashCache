import time
import threading


class NodeHealth:

    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"

    def __init__(
        self,
        failure_threshold=3,
        recovery_timeout=10
    ):

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.nodes = {}

        self.lock = threading.Lock()

    def add_node(self, node):

        with self.lock:

            self.nodes[node] = {
                "state": self.HEALTHY,
                "failures": 0,
                "last_failure": None
            }

    def remove_node(self, node):

        with self.lock:
            self.nodes.pop(node, None)

    def record_success(self, node):

        with self.lock:

            if node not in self.nodes:
                return

            self.nodes[node]["state"] = self.HEALTHY
            self.nodes[node]["failures"] = 0
            self.nodes[node]["last_failure"] = None

    def record_failure(self, node):

        with self.lock:

            if node not in self.nodes:
                return

            info = self.nodes[node]

            info["failures"] += 1
            info["last_failure"] = time.time()

            if info["failures"] >= self.failure_threshold:
                info["state"] = self.UNHEALTHY

    def is_healthy(self, node):

        with self.lock:

            if node not in self.nodes:
                return False

            info = self.nodes[node]

            if info["state"] == self.HEALTHY:
                return True

            if (
                info["last_failure"] is not None
                and time.time() - info["last_failure"]
                >= self.recovery_timeout
            ):
                return True

            return False

    def get_state(self, node):

        with self.lock:

            if node not in self.nodes:
                return self.UNHEALTHY

            return self.nodes[node]["state"]

    def get_status(self):

        with self.lock:

            return {
                node: info["state"]
                for node, info in self.nodes.items()
            }