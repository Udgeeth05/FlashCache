import time

from cache.early_expiration import EarlyExpiration


early_expiration = EarlyExpiration(beta=1.0)

now = time.time()

print("==============================")
print("Early Expiration Test")
print("==============================")


# Test 1: Already expired
expired_time = now - 1

result = early_expiration.should_refresh(
    expiration_time=expired_time,
    fetch_time=10
)

print("\nExpired entry:")
print("Should refresh:", result)


# Test 2: No fetch time
future_expiration = now + 5

result = early_expiration.should_refresh(
    expiration_time=future_expiration,
    fetch_time=0
)

print("\nNo fetch time:")
print("Should refresh:", result)


# Test 3: Entry close to expiration
# Remaining TTL = 1 second
# Original fetch time = 10 seconds
refresh_count = 0
total_tests = 1000

for _ in range(total_tests):

    result = early_expiration.should_refresh(
        expiration_time=now + 1,
        fetch_time=10
    )

    if result:
        refresh_count += 1


print("\nProbabilistic test:")
print("Tests:", total_tests)
print("Refreshes:", refresh_count)
print(
    "Refresh probability:",
    round(refresh_count / total_tests * 100, 2),
    "%"
)