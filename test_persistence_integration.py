import os
import shutil

from cache.engine import CacheEngine
from cache.persistence import CachePersistence


TEST_DIRECTORY = "integration_data"


if os.path.exists(TEST_DIRECTORY):

    shutil.rmtree(
        TEST_DIRECTORY
    )


print("==============================")
print("FlashCache Persistence Integration Test")
print("==============================")


print("\nCreating persistent cache:")

persistence = CachePersistence(
    directory=TEST_DIRECTORY
)

cache = CacheEngine(
    capacity=10,
    policy="LRU",
    persistence=persistence
)

print("Cache created")


print("\nWriting cache entries:")

cache.put(
    "product:1",
    {
        "name": "iPhone 17",
        "price": 99999
    },
    ttl=60
)

cache.put(
    "product:2",
    {
        "name": "Galaxy S25",
        "price": 89999
    },
    ttl=60
)

print(
    "Cache size:",
    cache.size()
)


print("\nReading from memory:")

print(
    "product:1:",
    cache.get("product:1")
)

print(
    "product:2:",
    cache.get("product:2")
)


print("\nChecking AOF:")

records = persistence.load_aof()

print(
    "AOF records:",
    len(records)
)

for record in records:

    print(record)


print("\nSimulating application restart:")

del cache


recovered_persistence = CachePersistence(
    directory=TEST_DIRECTORY
)

recovered_cache = CacheEngine(
    capacity=10,
    policy="LRU",
    persistence=recovered_persistence
)


print(
    "Recovered cache size:",
    recovered_cache.size()
)


print("\nReading recovered entries:")

product_1 = recovered_cache.get(
    "product:1"
)

product_2 = recovered_cache.get(
    "product:2"
)

print(
    "product:1:",
    product_1
)

print(
    "product:2:",
    product_2
)


if (
    product_1 is not None
    and product_2 is not None
):

    print(
        "\nPERSISTENCE INTEGRATION SUCCESS"
    )

else:

    print(
        "\nPERSISTENCE INTEGRATION FAILED"
    )