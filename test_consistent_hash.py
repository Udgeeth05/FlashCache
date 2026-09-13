from cache.consistent_hash import ConsistentHashRing


ring = ConsistentHashRing(
    virtual_nodes=50
)

ring.add_node("node-1")
ring.add_node("node-2")
ring.add_node("node-3")


print("==============================")
print("Consistent Hash Test")
print("==============================")

print("\nNodes:")
print(ring.get_nodes())

print("\nKey distribution:")

for key in [
    "user:1",
    "user:2",
    "user:3",
    "user:4",
    "user:5",
    "product:1",
    "product:2",
    "product:3"
]:

    print(
        key,
        "→",
        ring.get_node(key)
    )


print("\nRemoving node-2...")

ring.remove_node("node-2")

print("Remaining nodes:")
print(ring.get_nodes())

print("\nDistribution after removal:")

for key in [
    "user:1",
    "user:2",
    "user:3",
    "product:1",
    "product:2"
]:

    print(
        key,
        "→",
        ring.get_node(key)
    )