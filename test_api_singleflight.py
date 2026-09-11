import threading
import urllib.request
import time


URL = "http://127.0.0.1:8000/product/1"

results = []
lock = threading.Lock()


def request():

    start = time.perf_counter()

    with urllib.request.urlopen(URL) as response:
        data = response.read().decode()

    elapsed = time.perf_counter() - start

    with lock:
        results.append((data, elapsed))


threads = []

for i in range(10):
    thread = threading.Thread(target=request)
    threads.append(thread)


start = time.perf_counter()

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

total = time.perf_counter() - start


print()
print("==============================")
print("FlashCache SingleFlight Test")
print("==============================")
print("Requests:", len(results))
print("Total time:", round(total, 4), "seconds")

for i, (data, elapsed) in enumerate(results, 1):
    print(f"Request {i}: {round(elapsed, 4)}s → {data}")