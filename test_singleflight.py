import threading
import time

from cache.singleflight import SingleFlight


singleflight = SingleFlight()

database_calls = 0

counter_lock = threading.Lock()


def database_query():

    global database_calls

    with counter_lock:

        database_calls += 1

    print(
        threading.current_thread().name,
        "→ PostgreSQL"
    )

    time.sleep(1)

    return "iPhone 17"


def request():

    result = singleflight.do(
        "iphone",
        database_query
    )

    print(
        threading.current_thread().name,
        "→",
        result
    )


threads = []

for i in range(10):

    thread = threading.Thread(
        target=request,
        name=f"Request-{i + 1}"
    )

    threads.append(thread)


start = time.perf_counter()

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()


elapsed = time.perf_counter() - start


print()
print("======================")
print("SingleFlight Test")
print("======================")

print(
    "Requests:",
    len(threads)
)

print(
    "Database calls:",
    database_calls
)

print(
    "Total time:",
    round(elapsed, 2),
    "seconds"
)