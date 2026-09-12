import time

from cache.rate_limiter import TokenBucket


limiter = TokenBucket(
    capacity=3,
    refill_rate=1
)


print("==============================")
print("Rate Limiter Test")
print("==============================")


print("\nInitial burst:")

for i in range(5):

    allowed = limiter.allow("client-1")

    print(
        f"Request {i + 1} →",
        "ALLOWED" if allowed else "BLOCKED"
    )


print("\nWaiting for token refill...")

time.sleep(1.1)

allowed = limiter.allow("client-1")

print(
    "After 1 second →",
    "ALLOWED" if allowed else "BLOCKED"
)
