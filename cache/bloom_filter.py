import hashlib


class BloomFilter:

    def __init__(self, size=10000, hash_count=5):

        self.size = size
        self.hash_count = hash_count

        self.bits = bytearray(size)

    def _hashes(self, key):

        key = str(key).encode("utf-8")

        for i in range(self.hash_count):

            data = key + i.to_bytes(4, "little")

            digest = hashlib.sha256(data).digest()

            number = int.from_bytes(
                digest[:8],
                "little"
            )

            yield number % self.size

    def add(self, key):

        for index in self._hashes(key):

            self.bits[index] = 1

    def might_contain(self, key):

        for index in self._hashes(key):

            if self.bits[index] == 0:

                return False

        return True

    def clear(self):

        self.bits = bytearray(self.size)