from cache.engine import CacheEngine


cache = CacheEngine(
    capacity=3,
    policy="LRU"
)


print("Before inserting:")
print("iphone:", cache.get("iphone"))


print("\nAdding products...")

cache.put(
    "iphone",
    "iPhone 17"
)

cache.put(
    "samsung",
    "Galaxy S25"
)


print("\nAfter inserting:")

print(
    "iphone:",
    cache.get("iphone")
)

print(
    "samsung:",
    cache.get("samsung")
)

print(
    "pixel:",
    cache.get("pixel")
)