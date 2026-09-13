import time

from cache.node_health import NodeHealth


health = NodeHealth(
    failure_threshold=3,
    recovery_timeout=2
)


health.add_node("node-1")
health.add_node("node-2")


print("==============================")
print("Node Health Test")
print("==============================")


print("\nInitial:")
print(health.get_status())


print("\nRecording failures:")

for i in range(3):

    health.record_failure("node-1")

    print(
        f"Failure {i + 1} →",
        health.get_state("node-1")
    )


print("\nNode 2:")
print(
    health.get_state("node-2")
)


print("\nWaiting for recovery...")

time.sleep(2.1)

print(
    "Node 1 healthy:",
    health.is_healthy("node-1")
)