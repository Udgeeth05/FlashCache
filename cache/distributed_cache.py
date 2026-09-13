from cache.consistent_hash import ConsistentHashRing
from cache.engine import CacheEngine
from cache.node_health import NodeHealth


class DistributedCache:

    def __init__(
        self,
        nodes=None,
        capacity=100,
        policy="LRU",
        replicas=1
    ):

        self.capacity = capacity
        self.policy = policy
        self.replicas = replicas

        self.ring = ConsistentHashRing(
            virtual_nodes=100
        )

        self.health = NodeHealth(
            failure_threshold=3,
            recovery_timeout=10
        )

        self.nodes = {}

        if nodes:

            for node in nodes:
                self.add_node(node)

    def add_node(self, node):

        if node in self.nodes:
            return

        self.nodes[node] = CacheEngine(
            capacity=self.capacity,
            policy=self.policy
        )

        self.ring.add_node(node)
        self.health.add_node(node)

    def remove_node(self, node):

        if node not in self.nodes:
            return

        self.ring.remove_node(node)
        self.health.remove_node(node)

        del self.nodes[node]

    def _get_replica_nodes(self, key):

        if not self.ring.sorted_hashes:
            return []

        primary = self.ring.get_node(key)

        if primary is None:
            return []

        primary_hash = self.ring._hash(
            f"{primary}:0"
        )

        start_index = 0

        if primary_hash in self.ring.sorted_hashes:

            start_index = self.ring.sorted_hashes.index(
                primary_hash
            )

        selected = []
        seen = set()

        for offset in range(
            len(self.ring.sorted_hashes)
        ):

            index = (
                start_index + offset
            ) % len(self.ring.sorted_hashes)

            node = self.ring.ring[
                self.ring.sorted_hashes[index]
            ]

            if node not in seen:

                selected.append(node)
                seen.add(node)

            if len(selected) >= self.replicas + 1:
                break

        return selected

    def get(self, key):

        replica_nodes = self._get_replica_nodes(key)

        for node in replica_nodes:

            if not self.health.is_healthy(node):
                continue

            value = self.nodes[node].get(key)

            if value is not None:

                self.health.record_success(node)

                return value

        return None

    def put(self, key, value, ttl=300):

        replica_nodes = self._get_replica_nodes(key)

        for node in replica_nodes:

            if not self.health.is_healthy(node):
                continue

            try:

                self.nodes[node].put(
                    key,
                    value,
                    ttl
                )

                self.health.record_success(node)

            except Exception:

                self.health.record_failure(node)

    def delete(self, key):

        replica_nodes = self._get_replica_nodes(key)

        for node in replica_nodes:

            if not self.health.is_healthy(node):
                continue

            try:

                self.nodes[node].delete(key)
                self.health.record_success(node)

            except Exception:

                self.health.record_failure(node)

    def get_node(self, key):

        return self.ring.get_node(key)

    def get_nodes(self):

        return list(self.nodes.keys())

    def get_healthy_nodes(self):

        return [
            node
            for node in self.nodes
            if self.health.is_healthy(node)
        ]

    def mark_node_failure(self, node):

        for _ in range(
            self.health.failure_threshold
        ):
            self.health.record_failure(node)

    def recover_node(self, node):

        self.health.record_success(node)

    def get_health(self):

        return self.health.get_status()

    def size(self):

        total = 0

        for cache in self.nodes.values():
            total += cache.size()

        return total