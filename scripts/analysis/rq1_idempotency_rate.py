import csv
from collections import defaultdict
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Combined 5-run experimental results
INPUT_FILE = (
    PROJECT_ROOT
    / "results"
    / "Combined_Results"
    / "results_5runs_combined.csv"
)

MODELS = ["GPT", "Claude", "Qwen"]

stats = defaultdict(
    lambda: {
        "total": 0,
        "eligible": 0,
        "idempotent": 0,
    }
)

with open(INPUT_FILE, "r", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        model = row["model"]

        stats[model]["total"] += 1

        # Only functionally correct playbooks are eligible
        # for repeated-execution idempotency assessment.
        if row["functional_correct"] == "Yes":
            stats[model]["eligible"] += 1

            if row["repeated_idempotent"] == "Yes":
                stats[model]["idempotent"] += 1


print("\nRQ1: Repeated-Execution Idempotency")
print("=" * 68)

print(
    f"{'Model':<10}"
    f"{'Total':<10}"
    f"{'Eligible':<12}"
    f"{'Idempotent':<14}"
    f"{'IR (%)':<10}"
)

print("-" * 68)

overall_total = 0
overall_eligible = 0
overall_idempotent = 0

for model in MODELS:
    total = stats[model]["total"]
    eligible = stats[model]["eligible"]
    idempotent = stats[model]["idempotent"]

    ir = (
        (idempotent / eligible) * 100
        if eligible > 0
        else 0.0
    )

    print(
        f"{model:<10}"
        f"{total:<10}"
        f"{eligible:<12}"
        f"{idempotent:<14}"
        f"{ir:<10.2f}"
    )

    overall_total += total
    overall_eligible += eligible
    overall_idempotent += idempotent


overall_ir = (
    (overall_idempotent / overall_eligible) * 100
    if overall_eligible > 0
    else 0.0
)

print("-" * 68)

print(
    f"{'Overall':<10}"
    f"{overall_total:<10}"
    f"{overall_eligible:<12}"
    f"{overall_idempotent:<14}"
    f"{overall_ir:<10.2f}"
)

print("=" * 68)

print(
    "\nIR = Repeatedly Idempotent Playbooks / "
    "Functionally Correct (Eligible) Playbooks × 100"
)

# Save calculated results to CSV
OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "Analysis"
    / "Idempotency_Rates"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "idempotency_rates.csv"

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "Model",
        "Total_Playbooks",
        "Eligible_Playbooks",
        "Repeatedly_Idempotent",
        "Idempotency_Rate_Percent",
    ])

    for model in MODELS:
        total = stats[model]["total"]
        eligible = stats[model]["eligible"]
        idempotent = stats[model]["idempotent"]

        ir = (
            (idempotent / eligible) * 100
            if eligible > 0
            else 0.0
        )

        writer.writerow([
            model,
            total,
            eligible,
            idempotent,
            f"{ir:.2f}",
        ])

    writer.writerow([
        "Overall",
        overall_total,
        overall_eligible,
        overall_idempotent,
        f"{overall_ir:.2f}",
    ])

print(f"\nResults saved to: {OUTPUT_FILE}")