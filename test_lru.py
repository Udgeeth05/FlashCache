from cache.lru_cache import LRUCache


cache = LRUCache(capacity=3)

cache.put("A", "Apple")
cache.put("B", "Banana")
cache.put("C", "Cherry")

print("Initial size:", cache.size())

print("A:", cache.get("A"))

cache.put("D", "Durian")

print("A:", cache.get("A"))
print("B:", cache.get("B"))
print("C:", cache.get("C"))
print("D:", cache.get("D"))