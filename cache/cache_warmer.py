from cache.engine import CacheEngine


class CacheWarmer:

    def __init__(self, cache: CacheEngine):
        self.cache = cache

    def warm(self, keys, loader, ttl=300):

        warmed = 0
        skipped = 0

        for key in keys:

            key = str(key)

            # Skip keys that are already cached
            if self.cache.get(key) is not None:
                skipped += 1
                continue

            value = loader(key)

            if value is None:
                continue

            self.cache.put(
                key,
                value,
                ttl=ttl
            )

            warmed += 1

        return {
            "warmed": warmed,
            "skipped": skipped
        }