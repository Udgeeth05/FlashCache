import random
import time
import csv
import json
import os
import statistics
from unittest import result

from cache.engine import CacheEngine


def percentile(values, percentile):

    if not values:
        return 0

    values = sorted(values)

    index = int(len(values) * percentile / 100)

    if index >= len(values):
        index = len(values) - 1

    return values[index]


def generate_workload(
    workload_type="uniform",
    total_requests=10000,
    number_of_keys=1000
):

    workload = []

    # -----------------------------
    # Uniform workload
    # -----------------------------
    if workload_type == "uniform":

        for _ in range(total_requests):

            key = str(
                random.randint(
                    1,
                    number_of_keys
                )
            )

            workload.append(key)

    # -----------------------------
    # Hotspot workload
    # -----------------------------
    elif workload_type == "hotspot":

        hot_keys = [
            str(i)
            for i in range(1, 11)
        ]

        cold_keys = [
            str(i)
            for i in range(11, number_of_keys + 1)
        ]

        for _ in range(total_requests):

            # 80% requests go to hot keys
            if random.random() < 0.80:

                key = random.choice(
                    hot_keys
                )

            else:

                key = random.choice(
                    cold_keys
                )

            workload.append(key)

    # -----------------------------
    # Temporal workload
    # -----------------------------
    elif workload_type == "temporal":

        first_half = [
            str(i)
            for i in range(1, 101)
        ]

        second_half = [
            str(i)
            for i in range(901, 1001)
        ]

        for i in range(total_requests):

            if i < total_requests / 2:

                key = random.choice(
                    first_half
                )

            else:

                key = random.choice(
                    second_half
                )

            workload.append(key)

    else:

        raise ValueError(
            "Unknown workload type"
        )

    return workload


def benchmark(policy, workload, capacity=100):

    cache = CacheEngine(
        capacity=capacity,
        policy=policy
    )

    hits = 0
    misses = 0
    latencies = []

    for key in workload:

        start = time.perf_counter()

        value = cache.get(key)

        if value is not None:

            hits += 1

        else:

            misses += 1

            cache.put(
                key,
                f"value-{key}",
                ttl=300
            )

        end = time.perf_counter()

        latency = (end - start) * 1000

        latencies.append(latency)

    total_requests = hits + misses

    hit_rate = (
        hits / total_requests
    ) * 100

    miss_rate = (
        misses / total_requests
    ) * 100

    return {
        "policy": policy,
        "requests": total_requests,
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hit_rate, 2),
        "miss_rate": round(miss_rate, 2),
        "average_latency_ms": round(
            statistics.mean(latencies),
            4
        ),
        "p50_latency_ms": round(
            percentile(latencies, 50),
            4
        ),
        "p95_latency_ms": round(
            percentile(latencies, 95),
            4
        ),
        "p99_latency_ms": round(
            percentile(latencies, 99),
            4
        ),
        "evictions": cache.get_evictions()
    }

def save_results(results):

    results_dir = os.path.join(
        "benchmarks",
        "results"
    )

    os.makedirs(
        results_dir,
        exist_ok=True
    )

    # Save JSON
    json_path = os.path.join(
        results_dir,
        "results.json"
    )

    with open(
        json_path,
        "w"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    # Save CSV
    csv_path = os.path.join(
        results_dir,
        "results.csv"
    )

    if results:

        fieldnames = results[0].keys()

        with open(
            csv_path,
            "w",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            writer.writerows(results)

    print("\nResults saved:")
    print(json_path)
    print(csv_path)

def main():
    results = []
    workloads = [
        "uniform",
        "hotspot",
        "temporal"
    ]

    for workload_type in workloads:

        print("\n")
        print("=" * 60)
        print("WORKLOAD:", workload_type.upper())
        print("=" * 60)

        workload = generate_workload(
            workload_type=workload_type,
            total_requests=10000,
            number_of_keys=1000
        )

        for policy in ["LRU", "LFU", "ARC"]:

            result = benchmark(
                policy,
                workload,
                capacity=100
            )
            result["workload"] = workload_type
            results.append(result)

            print("\nPolicy:", result["policy"])

            print(
                "Hit Rate:",
                result["hit_rate"],
                "%"
            )

            print(
                "Miss Rate:",
                result["miss_rate"],
                "%"
            )

            print(
                "Average:",
                result["average_latency_ms"],
                "ms"
            )

            print(
                "P50:",
                result["p50_latency_ms"],
                "ms"
            )

            print(
                "P95:",
                result["p95_latency_ms"],
                "ms"
            )

            print(
                "P99:",
                result["p99_latency_ms"],
                "ms"
            )

            print(
                "Evictions:",
                result["evictions"]
            )
    save_results(results)

if __name__ == "__main__":
    main()