import csv
import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_FILE = (
    PROJECT_ROOT
    / "results"
    / "Combined_Results"
    / "results_5runs_combined.csv"
)

TASKS_FILE = PROJECT_ROOT / "tasks" / "tasks.json"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "Analysis"
    / "Model_Category_Comparison"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = ["GPT", "Claude", "Qwen"]


# --------------------------------------------------
# Load task categories
# --------------------------------------------------

with open(TASKS_FILE, "r", encoding="utf-8") as f:
    task_data = json.load(f)

task_categories = {
    task["id"]: task["category"]
    for task in task_data["tasks"]
}


# --------------------------------------------------
# Statistics helper
# --------------------------------------------------

def new_stats():
    return {
        "total": 0,
        "functional_correct": 0,
        "idempotent": 0,
        "non_idempotent": 0,
    }


model_stats = defaultdict(new_stats)
category_stats = defaultdict(new_stats)
model_category_stats = defaultdict(new_stats)


# --------------------------------------------------
# Load final 5-run results
# --------------------------------------------------

with open(RESULTS_FILE, "r", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:

        task_id = row["task_id"].strip()
        model = row["model"].strip()
        functional = row["functional_correct"].strip()
        repeated = row["repeated_idempotent"].strip()

        category = task_categories.get(
            task_id,
            "Unknown"
        )

        groups = [
            model_stats[model],
            category_stats[category],
            model_category_stats[(model, category)],
        ]

        for stats in groups:

            stats["total"] += 1

            # Only functionally correct playbooks
            # are eligible for idempotency assessment.
            if functional == "Yes":

                stats["functional_correct"] += 1

                if repeated == "Yes":
                    stats["idempotent"] += 1

                elif repeated == "No":
                    stats["non_idempotent"] += 1


# --------------------------------------------------
# Calculate idempotency rate
# --------------------------------------------------

def idempotency_rate(stats):

    eligible = stats["functional_correct"]

    if eligible == 0:
        return None

    return (
        stats["idempotent"]
        / eligible
        * 100
    )


# --------------------------------------------------
# Save model comparison
# --------------------------------------------------

model_output = OUTPUT_DIR / "model_comparison.csv"

with open(model_output, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Model",
        "Total_Playbooks",
        "Functionally_Correct",
        "Eligible",
        "Repeatedly_Idempotent",
        "Non_Idempotent",
        "Idempotency_Rate_Percent",
    ])

    for model in MODELS:

        s = model_stats[model]
        rate = idempotency_rate(s)

        writer.writerow([
            model,
            s["total"],
            s["functional_correct"],
            s["functional_correct"],
            s["idempotent"],
            s["non_idempotent"],
            f"{rate:.2f}" if rate is not None else "N/A",
        ])


# --------------------------------------------------
# Save category comparison
# --------------------------------------------------

category_output = OUTPUT_DIR / "category_comparison.csv"

with open(category_output, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Category",
        "Total_Playbooks",
        "Functionally_Correct",
        "Eligible",
        "Repeatedly_Idempotent",
        "Non_Idempotent",
        "Idempotency_Rate_Percent",
    ])

    for category in sorted(category_stats):

        s = category_stats[category]
        rate = idempotency_rate(s)

        writer.writerow([
            category,
            s["total"],
            s["functional_correct"],
            s["functional_correct"],
            s["idempotent"],
            s["non_idempotent"],
            f"{rate:.2f}" if rate is not None else "N/A",
        ])


# --------------------------------------------------
# Save model × category comparison
# --------------------------------------------------

mc_output = (
    OUTPUT_DIR
    / "model_category_comparison.csv"
)

with open(mc_output, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Model",
        "Category",
        "Total_Playbooks",
        "Functionally_Correct",
        "Eligible",
        "Repeatedly_Idempotent",
        "Non_Idempotent",
        "Idempotency_Rate_Percent",
    ])

    for model in MODELS:

        categories = sorted(
            category
            for m, category in model_category_stats
            if m == model
        )

        for category in categories:

            s = model_category_stats[
                (model, category)
            ]

            rate = idempotency_rate(s)

            writer.writerow([
                model,
                category,
                s["total"],
                s["functional_correct"],
                s["functional_correct"],
                s["idempotent"],
                s["non_idempotent"],
                f"{rate:.2f}"
                if rate is not None
                else "N/A",
            ])


# --------------------------------------------------
# Terminal summary
# --------------------------------------------------

print("\nRQ3: Model Comparison")
print("=" * 70)

for model in MODELS:

    s = model_stats[model]
    rate = idempotency_rate(s)

    print(
        f"{model:<10} "
        f"Eligible={s['functional_correct']:<3} "
        f"Idempotent={s['idempotent']:<3} "
        f"Non-Idempotent={s['non_idempotent']:<3} "
        f"IR={rate:.2f}%"
    )


print("\nRQ3: Category Comparison")
print("=" * 70)

for category in sorted(category_stats):

    s = category_stats[category]
    rate = idempotency_rate(s)

    print(
        f"{category:<40} "
        f"Eligible={s['functional_correct']:<3} "
        f"Idempotent={s['idempotent']:<3} "
        f"Non-Idempotent={s['non_idempotent']:<3} "
        f"IR={rate:.2f}%"
    )


print("\nResults saved to:")
print(OUTPUT_DIR)
