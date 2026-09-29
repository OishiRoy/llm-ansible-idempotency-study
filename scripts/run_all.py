import subprocess
import sys
from pathlib import Path

# Usage:
# python scripts/run_all.py GPT default

if len(sys.argv) != 3:
    print("Usage: python scripts/run_all.py <MODEL> <CONDITION>")
    sys.exit(1)

model = sys.argv[1]
condition = sys.argv[2]

base_dir = Path(f"generated/{model}/{condition}")

if not base_dir.exists():
    print(f"ERROR: Folder not found: {base_dir}")
    sys.exit(1)

# Find P01.yml ... P30.yml directly inside the condition folder
playbooks = sorted(base_dir.glob("P*.yml"))

if not playbooks:
    print(f"ERROR: No playbooks found in {base_dir}")
    sys.exit(1)

print("")
print("#" * 70)
print(f"MODEL: {model} | CONDITION: {condition}")
print("#" * 70)
print(f"Found {len(playbooks)} playbooks.")

total_completed = 0
total_failed = 0

for playbook in playbooks:
    task_id = playbook.stem

    print("")
    print("=" * 70)
    print(f"Running {task_id} | {model} | {condition}")
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_experiment.py",
            task_id,
            model,
            condition
        ]
    )

    if result.returncode != 0:
        print(f"{task_id}: FAILED")
        total_failed += 1
    else:
        print(f"{task_id}: COMPLETED")
        total_completed += 1

print("")
print("#" * 70)
print("BATCH TESTING FINISHED")
print("#" * 70)
print(f"Model: {model}")
print(f"Condition: {condition}")
print(f"Playbooks found: {len(playbooks)}")
print(f"Completed: {total_completed}")
print(f"Failed: {total_failed}")