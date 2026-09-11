import time
from cache.circuit_breaker import CircuitBreaker


breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=2
)


print("Initial state:", breaker.get_state())


print("\nRecording failures...")

for i in range(3):

    breaker.record_failure()

    print(
        f"Failure {i + 1} →",
        breaker.get_state()
    )


print("\nAllow request while OPEN:")

print(
    "Allowed:",
    breaker.allow_request()
)


print("\nWaiting for recovery timeout...")

time.sleep(2.1)


print(
    "Allowed after timeout:",
    breaker.allow_request()
)

print(
    "State:",
    breaker.get_state()
)


print("\nRecording successful request...")

breaker.record_success()

print(
    "Final state:",
    breaker.get_state()
)