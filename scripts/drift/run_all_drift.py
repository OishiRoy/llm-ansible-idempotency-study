import csv
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "scripts" / "drift")
)

from drift_rules import SELECTED_DRIFT_TASKS


MODELS = ["GPT", "Claude", "Qwen"]
CONDITION = "default"

RESULTS_FILE = (
    PROJECT_ROOT
    / "results"
    / "Drift_Experiment"
    / "drift_results.csv"
)

RUNNER = (
    PROJECT_ROOT
    / "scripts"
    / "drift"
    / "run_drift_experiment.py"
)


def get_completed_cases():
    completed = set()

    if not RESULTS_FILE.exists():
        return completed

    with open(RESULTS_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            task_id = row.get("task_id")
            model = row.get("model")
            condition = row.get("condition")

            if task_id and model and condition:
                completed.add(
                    (task_id, model, condition)
                )

    return completed


completed_cases = get_completed_cases()

total = len(SELECTED_DRIFT_TASKS) * len(MODELS)
completed_now = 0
skipped = 0
failed = 0


print("======================================")
print(" CONTROLLED DRIFT EXPERIMENT")
print("======================================")
print(f"Models: {', '.join(MODELS)}")
print(
    "Tasks: "
    + ", ".join(SELECTED_DRIFT_TASKS)
)
print(f"Total cases: {total}")
print("")


for model in MODELS:
    for task_id in SELECTED_DRIFT_TASKS:

        case = (
            task_id,
            model,
            CONDITION
        )

        print("--------------------------------------")
        print(
            f"Case: {task_id} | "
            f"{model} | {CONDITION}"
        )

        if case in completed_cases:
            print("Already present in CSV -> SKIPPED")
            skipped += 1
            continue

        command = [
            sys.executable,
            str(RUNNER),
            task_id,
            model,
            CONDITION
        ]

        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT
        )

        if result.returncode == 0:
            print(
                f"{task_id} | {model}: COMPLETED"
            )
            completed_now += 1
        else:
            print(
                f"{task_id} | {model}: FAILED"
            )
            failed += 1


print("")
print("======================================")
print(" DRIFT EXPERIMENT SUMMARY")
print("======================================")
print(f"Total planned cases : {total}")
print(f"Already completed   : {skipped}")
print(f"Completed this run  : {completed_now}")
print(f"Failed              : {failed}")
print("")
print(f"Results: {RESULTS_FILE}")
