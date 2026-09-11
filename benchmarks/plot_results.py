import pandas as pd
import matplotlib.pyplot as plt
import os


RESULTS_FILE = "benchmarks/results/results.csv"
RESULTS_DIR = "benchmarks/results"


df = pd.read_csv(RESULTS_FILE)


workloads = df["workload"].unique()


for workload in workloads:

    data = df[df["workload"] == workload]

    plt.figure(figsize=(8, 5))

    plt.bar(
        data["policy"],
        data["hit_rate"]
    )

    plt.title(
        f"FlashCache Hit Rate - {workload.title()} Workload"
    )

    plt.xlabel("Cache Policy")

    plt.ylabel("Hit Rate (%)")

    plt.ylim(0, 100)

    plt.tight_layout()

    output_file = os.path.join(
        RESULTS_DIR,
        f"{workload}_hit_rate.png"
    )

    plt.savefig(output_file)

    plt.close()

    print(f"Generated: {output_file}")


print("\nAll graphs generated successfully.")