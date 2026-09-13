import hashlib
import bisect


class ConsistentHashRing:

    def __init__(self, virtual_nodes=100):

        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_hashes = []

    def _hash(self, value):

        digest = hashlib.sha256(
            str(value).encode("utf-8")
        ).hexdigest()

        return int(digest, 16)

    def add_node(self, node):

        for i in range(self.virtual_nodes):

            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)

            self.ring[hash_value] = node

        self.sorted_hashes = sorted(
            self.ring.keys()
        )

    def remove_node(self, node):

        hashes_to_remove = [
            hash_value
            for hash_value, owner in self.ring.items()
            if owner == node
        ]

        for hash_value in hashes_to_remove:
            del self.ring[hash_value]

        self.sorted_hashes = sorted(
            self.ring.keys()
        )

    def get_node(self, key):

        if not self.ring:
            return None

        hash_value = self._hash(key)

        index = bisect.bisect(
            self.sorted_hashes,
            hash_value
        )

        if index == len(self.sorted_hashes):
            index = 0

        return self.ring[
            self.sorted_hashes[index]
        ]

    def get_nodes(self):

        return sorted(
            set(self.ring.values())
        )