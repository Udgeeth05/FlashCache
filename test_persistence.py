from cache.persistence import CachePersistence


persistence = CachePersistence(
    directory="test_data"
)


print("==============================")
print("FlashCache Persistence Test")
print("==============================")


print("\nWriting AOF records:")

persistence.append(
    "PUT",
    "product:1",
    {
        "name": "iPhone 17",
        "price": 99999
    },
    ttl=60
)

persistence.append(
    "DELETE",
    "product:2"
)

print("AOF written")


print("\nReading AOF:")

records = persistence.load_aof()

for record in records:
    print(record)


print("\nCreating snapshot:")

snapshot_data = {
    "product:1": {
        "name": "iPhone 17",
        "price": 99999
    },
    "product:2": {
        "name": "Galaxy S25",
        "price": 89999
    }
}

persistence.snapshot(
    snapshot_data
)

print("Snapshot created")


print("\nLoading snapshot:")

loaded = persistence.load_snapshot()

print(loaded)


if (
    loaded.get("product:1", {}).get("name")
    == "iPhone 17"
):

    print("\nPERSISTENCE SUCCESS")

else:

    print("\nPERSISTENCE FAILED")