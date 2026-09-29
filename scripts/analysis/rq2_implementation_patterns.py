from pathlib import Path
import csv
import re
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GENERATED_DIR = PROJECT_ROOT / "generated"
RESULTS_FILE = (
    PROJECT_ROOT
    / "results"
    / "Combined_Results"
    / "results_5runs_combined.csv"
)

MODELS = ["GPT", "Claude", "Qwen"]

PATTERNS = {
    "apt": r"(?m)^\s+(?:ansible\.builtin\.)?apt:",
    "file": r"(?m)^\s+(?:ansible\.builtin\.)?file:",
    "lineinfile": r"(?m)^\s+(?:ansible\.builtin\.)?lineinfile:",
    "blockinfile": r"(?m)^\s+(?:ansible\.builtin\.)?blockinfile:",
    "copy": r"(?m)^\s+(?:ansible\.builtin\.)?copy:",
    "template": r"(?m)^\s+(?:ansible\.builtin\.)?template:",
    "service": r"(?m)^\s+(?:ansible\.builtin\.)?service:",
    "systemd": r"(?m)^\s+(?:ansible\.builtin\.)?systemd:",
    "cron": r"(?m)^\s+(?:ansible\.builtin\.)?cron:",
    "user": r"(?m)^\s+(?:ansible\.builtin\.)?user:",
    "authorized_key": r"(?m)^\s+(?:ansible\.posix\.)?authorized_key:",
    "unarchive": r"(?m)^\s+(?:ansible\.builtin\.)?unarchive:",
    "command": r"(?m)^\s+(?:ansible\.builtin\.)?command:",
    "shell": r"(?m)^\s+(?:ansible\.builtin\.)?shell:",
    "dpkg_selections": r"(?m)^\s+(?:ansible\.builtin\.)?dpkg_selections:",
    "creates_guard": r"(?m)^\s+creates:",
    "changed_when": r"(?m)^\s+changed_when:",
    "update_cache": r"(?m)^\s+update_cache:\s*true\s*$",
}

# Load experimental outcomes
outcomes = {}

with open(RESULTS_FILE, "r", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        key = (row["model"], row["task_id"])

        outcomes[key] = {
            "functional_correct": row["functional_correct"],
            "repeated_idempotent": row["repeated_idempotent"].strip(),
        }

pattern_stats = defaultdict(
    lambda: {
        "total": 0,
        "eligible": 0,
        "idempotent": 0,
        "non_idempotent": 0,
    }
)

print("\nRQ2: Implementation Pattern Analysis")
print("=" * 75)

for model in MODELS:
    playbook_dir = GENERATED_DIR / model / "default"

    for playbook in sorted(playbook_dir.glob("P*.yml")):
        task_id = playbook.stem
        text = playbook.read_text(encoding="utf-8")

        outcome = outcomes.get((model, task_id))

        if not outcome:
            continue

        for pattern_name, regex in PATTERNS.items():

            if re.search(regex, text):

                pattern_stats[pattern_name]["total"] += 1

                if outcome["functional_correct"] == "Yes":
                    pattern_stats[pattern_name]["eligible"] += 1

                    if outcome["repeated_idempotent"] == "Yes":
                        pattern_stats[pattern_name]["idempotent"] += 1

                    elif outcome["repeated_idempotent"] == "No":
                        pattern_stats[pattern_name]["non_idempotent"] += 1


print(
    f"{'Pattern':<20}"
    f"{'Used':<10}"
    f"{'Eligible':<12}"
    f"{'Idempotent':<14}"
    f"{'Non-Idempotent':<15}"
)

print("-" * 75)

for pattern, values in sorted(pattern_stats.items()):
    print(
        f"{pattern:<20}"
        f"{values['total']:<10}"
        f"{values['eligible']:<12}"
        f"{values['idempotent']:<14}"
        f"{values['non_idempotent']:<15}"
    )

print("=" * 75)

# Save implementation-pattern analysis to CSV
OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "Analysis"
    / "Implementation_Patterns"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "implementation_patterns.csv"

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "Pattern",
        "Total_Usages",
        "Eligible_Usages",
        "Idempotent_Usages",
        "Non_Idempotent_Usages",
    ])

    for pattern, values in sorted(pattern_stats.items()):
        writer.writerow([
            pattern,
            values["total"],
            values["eligible"],
            values["idempotent"],
            values["non_idempotent"],
        ])

print(f"\nResults saved to: {OUTPUT_FILE}")