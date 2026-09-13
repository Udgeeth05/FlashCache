from cache.distributed_cache import DistributedCache


cache = DistributedCache(
    nodes=[
        "node-1",
        "node-2",
        "node-3"
    ],
    capacity=10,
    policy="LRU",
    replicas=1
)


print("==============================")
print("Distributed Failover Test")
print("==============================")


key = "product:1"
value = "iPhone 17"


print("\nCluster:")
print(cache.get_nodes())


print("\nWriting value:")

cache.put(
    key,
    value,
    ttl=60
)

print("Primary:", cache.get_node(key))
print("Value:", cache.get(key))


print("\nHealth before failure:")
print(cache.get_health())


primary = cache.get_node(key)

print("\nSimulating primary failure:")
print(primary)

cache.mark_node_failure(primary)

print("\nHealth after failure:")
print(cache.get_health())


print("\nReading after primary failure:")

result = cache.get(key)

print("Value:", result)


print("\nHealthy nodes:")
print(cache.get_healthy_nodes())


print("\nFailover result:")

if result == value:
    print("FAILOVER SUCCESS")
else:
    print("FAILOVER FAILED")