from cache.bloom_filter import BloomFilter


bloom = BloomFilter(
    size=10000,
    hash_count=5
)


# Add existing products

bloom.add("iphone")

bloom.add("samsung")

bloom.add("pixel")


print(
    "iphone:",
    bloom.might_contain("iphone")
)

print(
    "samsung:",
    bloom.might_contain("samsung")
)

print(
    "pixel:",
    bloom.might_contain("pixel")
)

print(
    "nokia-999:",
    bloom.might_contain("nokia-999")
)

print(
    "random-product-123:",
    bloom.might_contain(
        "random-product-123"
    )
)
print(
    "Definitely nonexistent:",
    bloom.might_contain("this-product-definitely-does-not-exist")
)