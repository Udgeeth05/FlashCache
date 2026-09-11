from cache.arc_cache import ARCCache


cache = ARCCache(capacity=3)

cache.put("A", "Apple")
cache.put("B", "Banana")
cache.put("C", "Cherry")

print("A:", cache.get("A"))

cache.put("D", "Durian")

print("A:", cache.get("A"))
print("B:", cache.get("B"))
print("C:", cache.get("C"))
print("D:", cache.get("D"))

print("Cache size:", cache.size())