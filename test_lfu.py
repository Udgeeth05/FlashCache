from cache.lfu_cache import LFUCache


cache = LFUCache(capacity=3)

cache.put("A", "Apple")
cache.put("B", "Banana")
cache.put("C", "Cherry")

# Increase frequency of A
cache.get("A")
cache.get("A")
cache.get("A")

# Increase frequency of C
cache.get("C")

# B has the lowest frequency
cache.put("D", "Durian")

print("A:", cache.get("A"))
print("B:", cache.get("B"))
print("C:", cache.get("C"))
print("D:", cache.get("D"))

print("Cache size:", cache.size())