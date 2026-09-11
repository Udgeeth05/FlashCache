from cache.simple_cache import SimpleCache

c = SimpleCache()
c.put("iphone", "iPhone 17 - $999", ttl=5)

print(c.get("iphone"))   # should print the value

import time
time.sleep(6)

print(c.get("iphone"))   # should print None, because it expired