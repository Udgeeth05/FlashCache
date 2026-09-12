from cache.engine import CacheEngine


cache = CacheEngine(
    capacity=10,
    policy="LRU"
)


print("==============================")
print("Payload Limit Test")
print("==============================")


small_payload = "hello"

cache.put(
    "small",
    small_payload,
    ttl=60
)

print("Small payload → ALLOWED")


large_payload = "x" * (5 * 1024 * 1024 + 1)

try:

    cache.put(
        "large",
        large_payload,
        ttl=60
    )

    print("Large payload → UNEXPECTEDLY ALLOWED")

except ValueError as error:

    print("Large payload → BLOCKED")
    print("Reason:", error)