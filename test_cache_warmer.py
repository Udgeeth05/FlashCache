from cache.engine import CacheEngine
from cache.cache_warmer import CacheWarmer


cache = CacheEngine(
    capacity=10,
    policy="LRU"
)

warmer = CacheWarmer(cache)


def fake_loader(key):

    products = {
        "1": "iPhone 17",
        "2": "Galaxy S25",
        "3": "Pixel 10"
    }

    return products.get(key)


print("==============================")
print("Cache Warmer Test")
print("==============================")


print("\nBefore warming:")

for key in ["1", "2", "3"]:
    print(key, "→", cache.get(key))


result = warmer.warm(
    keys=["1", "2", "3"],
    loader=fake_loader,
    ttl=60
)

print("\nWarming result:")
print(result)


print("\nAfter warming:")

for key in ["1", "2", "3"]:
    print(key, "→", cache.get(key))


result = warmer.warm(
    keys=["1", "2", "3"],
    loader=fake_loader,
    ttl=60
)

print("\nSecond warming:")
print(result)