import json
import os
import urllib.error
import urllib.parse
import urllib.request

from cache.consistent_hash import ConsistentHashRing


class NetworkDistributedCache:

    def __init__(
        self,
        node_urls=None,
        fallback_cache=None,
        replicas=2,
        timeout=2
    ):

        self.node_urls = [
            url.rstrip("/")
            for url in (node_urls or [])
        ]

        self.fallback_cache = fallback_cache

        self.replicas = max(
            0,
            min(
                replicas,
                max(0, len(self.node_urls) - 1)
            )
        )

        self.timeout = timeout

        self.ring = ConsistentHashRing(
            virtual_nodes=100
        )

        for node_url in self.node_urls:

            self.ring.add_node(
                node_url
            )

    @classmethod
    def from_environment(
        cls,
        fallback_cache=None
    ):

        raw_urls = os.getenv(
            "FLASHCACHE_NODE_URLS",
            ""
        )

        node_urls = [
            url.strip().rstrip("/")
            for url in raw_urls.split(",")
            if url.strip()
        ]

        return cls(
            node_urls=node_urls,
            fallback_cache=fallback_cache
        )

    def _request(
        self,
        method,
        url,
        body=None
    ):

        data = None

        headers = {
            "Content-Type": "application/json"
        }

        if body is not None:

            data = json.dumps(
                body
            ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method
        )

        with urllib.request.urlopen(
            request,
            timeout=self.timeout
        ) as response:

            raw = response.read()

            if not raw:

                return {}

            return json.loads(
                raw.decode("utf-8")
            )

    def _cache_url(
        self,
        node,
        key
    ):

        encoded_key = urllib.parse.quote(
            str(key),
            safe=""
        )

        return (
            f"{node}/cache/"
            f"{encoded_key}"
        )

    def _get_replica_nodes(
        self,
        key
    ):

        if not self.node_urls:

            return []

        if not self.ring.sorted_hashes:

            return []

        key_hash = self.ring._hash(
            str(key)
        )

        # Find the first virtual node clockwise
        # from the key hash.
        start_index = 0

        for index, hash_value in enumerate(
            self.ring.sorted_hashes
        ):

            if hash_value >= key_hash:

                start_index = index

                break

        selected = []

        seen = set()

        total_nodes = min(
            len(self.node_urls),
            self.replicas + 1
        )

        for offset in range(
            len(self.ring.sorted_hashes)
        ):

            index = (
                start_index + offset
            ) % len(
                self.ring.sorted_hashes
            )

            node = self.ring.ring[
                self.ring.sorted_hashes[index]
            ]

            if node in seen:

                continue

            selected.append(
                node
            )

            seen.add(node)

            if len(selected) >= total_nodes:

                break

        return selected

    def get(
        self,
        key
    ):

        key = str(key)

        nodes = self._get_replica_nodes(
            key
        )

        if not nodes:

            if self.fallback_cache is not None:

                return self.fallback_cache.get(
                    key
                )

            return None

        for node in nodes:

            try:

                result = self._request(
                    "GET",
                    self._cache_url(
                        node,
                        key
                    )
                )

                return result.get(
                    "value"
                )

            except urllib.error.HTTPError as error:

                if error.code == 404:

                    continue

            except Exception:

                continue

        return None

    def put(
        self,
        key,
        value,
        ttl=300
    ):

        key = str(key)

        nodes = self._get_replica_nodes(
            key
        )

        if not nodes:

            if self.fallback_cache is not None:

                self.fallback_cache.put(
                    key,
                    value,
                    ttl
                )

            return

        successful = 0

        for node in nodes:

            try:

                self._request(
                    "PUT",
                    self._cache_url(
                        node,
                        key
                    ),
                    {
                        "value": value,
                        "ttl": ttl
                    }
                )

                successful += 1

            except Exception:

                continue

        # If no network node accepted the write,
        # preserve the value in the local fallback.
        if successful == 0:

            if self.fallback_cache is not None:

                self.fallback_cache.put(
                    key,
                    value,
                    ttl
                )

    def delete(
        self,
        key
    ):

        key = str(key)

        nodes = self._get_replica_nodes(
            key
        )

        if not nodes:

            if self.fallback_cache is not None:

                self.fallback_cache.delete(
                    key
                )

            return

        for node in nodes:

            try:

                self._request(
                    "DELETE",
                    self._cache_url(
                        node,
                        key
                    )
                )

            except Exception:

                continue

    def get_node(
        self,
        key
    ):

        return self.ring.get_node(
            str(key)
        )

    def get_nodes(self):

        return list(
            self.node_urls
        )

    def get_healthy_nodes(self):

        healthy = []

        for node in self.node_urls:

            try:

                result = self._request(
                    "GET",
                    f"{node}/health"
                )

                if result.get("status") == "healthy":

                    healthy.append(
                        node
                    )

            except Exception:

                continue

        return healthy

    def size(self):

        total = 0

        for node in self.node_urls:

            try:

                result = self._request(
                    "GET",
                    f"{node}/node"
                )

                total += int(
                    result.get(
                        "cache_size",
                        0
                    )
                )

            except Exception:

                continue

        if (
            total == 0
            and self.fallback_cache is not None
        ):

            return self.fallback_cache.size()

        return total

    def memory_bytes(self):

        total = 0

        for node in self.node_urls:

            try:

                result = self._request(
                    "GET",
                    f"{node}/node"
                )

                total += int(
                    result.get(
                        "memory_bytes",
                        0
                    )
                )

            except Exception:

                continue

        if (
            total == 0
            and self.fallback_cache is not None
        ):

            return self.fallback_cache.memory_bytes()

        return total