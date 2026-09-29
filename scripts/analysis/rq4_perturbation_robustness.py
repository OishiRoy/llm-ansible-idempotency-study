import csv
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "results"
    / "Drift_Experiment"
    / "drift_results.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "Analysis"
    / "Perturbation_Robustness"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "perturbation_robustness.csv"

MODELS = ["GPT", "Claude", "Qwen"]


# --------------------------------------------------
# Statistics structure
# --------------------------------------------------

def new_stats():
    return {
        "total": 0,
        "eligible": 0,
        "drift_verified": 0,
        "recovery_success": 0,
        "recovery_verified": 0,
        "post_recovery_success": 0,
        "post_recovery_stable": 0,
    }


model_stats = defaultdict(new_stats)
overall = new_stats()


# --------------------------------------------------
# Load final controlled-perturbation results
# --------------------------------------------------

with open(INPUT_FILE, "r", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:

        model = row["model"].strip()

        # A case is eligible only when the initial
        # playbook execution successfully established
        # the intended functional state.
        eligible = (
            row["initial_run_success"].strip() == "Yes"
            and row["initial_functional"].strip() == "Yes"
        )

        model_stats[model]["total"] += 1
        overall["total"] += 1

        if not eligible:
            continue

        model_stats[model]["eligible"] += 1
        overall["eligible"] += 1

        if row["drift_verified"].strip() == "Yes":
            model_stats[model]["drift_verified"] += 1
            overall["drift_verified"] += 1

        if row["recovery_success"].strip() == "Yes":
            model_stats[model]["recovery_success"] += 1
            overall["recovery_success"] += 1

        if row["recovery_verified"].strip() == "Yes":
            model_stats[model]["recovery_verified"] += 1
            overall["recovery_verified"] += 1

        if row["post_recovery_success"].strip() == "Yes":
            model_stats[model]["post_recovery_success"] += 1
            overall["post_recovery_success"] += 1

        if row["post_recovery_stable"].strip() == "Yes":
            model_stats[model]["post_recovery_stable"] += 1
            overall["post_recovery_stable"] += 1


# --------------------------------------------------
# Percentage helper
# --------------------------------------------------

def percentage(value, denominator):
    if denominator == 0:
        return 0.0

    return (value / denominator) * 100


# --------------------------------------------------
# Print model-wise results
# --------------------------------------------------

print("\nRQ4: Controlled State-Perturbation Robustness")
print("=" * 100)

print(
    f"{'Model':<10}"
    f"{'Total':<8}"
    f"{'Eligible':<10}"
    f"{'Drift Verified':<16}"
    f"{'Recovery Verified':<19}"
    f"{'Post-Recovery Stable':<22}"
    f"{'Stable (%)':<12}"
)

print("-" * 100)

for model in MODELS:

    s = model_stats[model]

    stable_rate = percentage(
        s["post_recovery_stable"],
        s["eligible"]
    )

    print(
        f"{model:<10}"
        f"{s['total']:<8}"
        f"{s['eligible']:<10}"
        f"{s['drift_verified']:<16}"
        f"{s['recovery_verified']:<19}"
        f"{s['post_recovery_stable']:<22}"
        f"{stable_rate:<12.2f}"
    )


# --------------------------------------------------
# Overall results
# --------------------------------------------------

overall_stable_rate = percentage(
    overall["post_recovery_stable"],
    overall["eligible"]
)

print("-" * 100)

print(
    f"{'Overall':<10}"
    f"{overall['total']:<8}"
    f"{overall['eligible']:<10}"
    f"{overall['drift_verified']:<16}"
    f"{overall['recovery_verified']:<19}"
    f"{overall['post_recovery_stable']:<22}"
    f"{overall_stable_rate:<12.2f}"
)

print("=" * 100)


# --------------------------------------------------
# Save results to CSV
# --------------------------------------------------

with open(OUTPUT_FILE, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Model",
        "Total_Cases",
        "Eligible_Cases",
        "Drift_Verified",
        "Recovery_Success",
        "Recovery_Verified",
        "Post_Recovery_Success",
        "Post_Recovery_Stable",
        "Recovery_Rate_Percent",
        "Post_Recovery_Stability_Rate_Percent",
    ])

    for model in MODELS:

        s = model_stats[model]

        recovery_rate = percentage(
            s["recovery_verified"],
            s["eligible"]
        )

        stable_rate = percentage(
            s["post_recovery_stable"],
            s["eligible"]
        )

        writer.writerow([
            model,
            s["total"],
            s["eligible"],
            s["drift_verified"],
            s["recovery_success"],
            s["recovery_verified"],
            s["post_recovery_success"],
            s["post_recovery_stable"],
            f"{recovery_rate:.2f}",
            f"{stable_rate:.2f}",
        ])

    overall_recovery_rate = percentage(
        overall["recovery_verified"],
        overall["eligible"]
    )

    writer.writerow([
        "Overall",
        overall["total"],
        overall["eligible"],
        overall["drift_verified"],
        overall["recovery_success"],
        overall["recovery_verified"],
        overall["post_recovery_success"],
        overall["post_recovery_stable"],
        f"{overall_recovery_rate:.2f}",
        f"{overall_stable_rate:.2f}",
    ])


print(f"\nResults saved to: {OUTPUT_FILE}")
