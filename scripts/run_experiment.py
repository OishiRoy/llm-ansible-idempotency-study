import subprocess
import sys
import re
import csv
from pathlib import Path

from task_rules import TASK_RULES
from inject_drift import inject_curl_drift

DRIFT_INJECTION_TASKS = {"P03"}

# Usage:
# python scripts/run_experiment.py P01 GPT default

if len(sys.argv) != 4:
    print(
        "Usage: python scripts/run_experiment.py "
        "<TASK_ID> <MODEL> <CONDITION>"
    )
    sys.exit(1)

task_id = sys.argv[1]
model = sys.argv[2]
condition = sys.argv[3]

playbook = Path(
    f"generated/{model}/{condition}/{task_id}.yml"
)
log_dir = Path(
    f"logs/{model}/{condition}/{task_id}"
)
results_file = Path(f"results/{model}/results_5runs.csv")

if not playbook.exists():
    print(f"ERROR: Playbook not found: {playbook}")
    sys.exit(1)

log_dir.mkdir(parents=True, exist_ok=True)

container_name = (
    f"{task_id.lower()}-{model.lower()}-{condition}"
).replace("_", "-")


def run(command):
    return subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True
    )


def save_log(filename, result):
    path = log_dir / filename
    with open(path, "w") as f:
        f.write(result.stdout)
        f.write(result.stderr)


def parse_recap(text):
    match = re.search(
        r"ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)",
        text
    )

    if not match:
        return None

    return {
        "ok": int(match.group(1)),
        "changed": int(match.group(2)),
        "unreachable": int(match.group(3)),
        "failed": int(match.group(4))
    }


def setup_task():
    rule = TASK_RULES.get(task_id)

    if not rule:
        return True

    for command in rule.get("setup", []):
        result = run(
            f"docker exec {container_name} bash -c {command!r}"
        )

        with open(log_dir / "task_setup.txt", "a") as f:
            f.write(f"$ {command}\n")
            f.write(result.stdout)
            f.write(result.stderr)
            f.write("\n")

        if result.returncode != 0:
            return False

    return True


def verify_task():
    rule = TASK_RULES.get(task_id)

    if not rule:
        return None

    command = rule.get("verify")

    if not command:
        return None

    result = subprocess.run(
        ["docker", "exec", container_name, "bash", "-c", command],
        text=True,
        capture_output=True
    )

    save_log("verification.txt", result)

    return result.returncode == 0


def append_result(run1_stats, repeat_stats, syntax_valid, functional_correct):
    results_file.parent.mkdir(parents=True, exist_ok=True)

    file_exists = results_file.exists()

    eligible = (
        run1_stats is not None
        and run1_stats["failed"] == 0
        and functional_correct is True
    )

    repeated_idempotent = (
        eligible
        and all(
            repeat_stats.get(r) is not None
            and repeat_stats[r]["failed"] == 0
            and repeat_stats[r]["changed"] == 0
            for r in range(2, 6)
        )
    )

    row = {
        "task_id": task_id,
        "model": model,
        "condition": condition,
        "syntax_valid": "Yes" if syntax_valid else "No",
        "run1_success": (
            "Yes"
            if run1_stats and run1_stats["failed"] == 0
            else "No"
        ),
        "functional_correct": (
            "Yes" if functional_correct is True
            else "No" if functional_correct is False
            else "NotChecked"
        ),
        "run1_changed": run1_stats["changed"] if run1_stats else "",
    }

    for r in range(2, 6):
        stats = repeat_stats.get(r)

        row[f"run{r}_success"] = (
            "Yes" if stats and stats["failed"] == 0 else "No"
        )
        row[f"run{r}_changed"] = (
            stats["changed"] if stats else ""
        )

    row["repeated_idempotent"] = (
        "Yes" if eligible and repeated_idempotent
        else "No" if eligible and not repeated_idempotent
        else "N/A"
    )

    fieldnames = [
        "task_id",
        "model",
        "condition",
        "syntax_valid",
        "run1_success",
        "functional_correct",
        "run1_changed",
        "run2_success",
        "run2_changed",
        "run3_success",
        "run3_changed",
        "run4_success",
        "run4_changed",
        "run5_success",
        "run5_changed",
        "repeated_idempotent"
    ]

    with open(results_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


# 1. Create fresh fixed benchmark container
print(
    f"[{task_id} | {model}] "
    "Creating fresh fixed benchmark container..."
)

run(f"docker rm -f {container_name}")

create = run(
    f"docker run -d "
    f"--name {container_name} "
    f"--privileged "
    f"--init "
    f"ansible-idempotency-benchmark:v1 sleep infinity"
)

if create.returncode != 0:
    print(create.stderr)
    sys.exit(1)

try:
    # 2. Prepare container
    print(f"[{task_id}] Preparing container...")

    prep = run(
        f"docker exec {container_name} "
        f"bash -c 'python3 --version && ansible --version'"
    )

    save_log("container_setup.txt", prep)

    if prep.returncode != 0:
        print("Container preparation FAILED")
        sys.exit(1)

    # 3. Copy generated playbook
    copy_result = run(
        f'docker cp "{playbook}" {container_name}:/playbook.yml'
    )

    if copy_result.returncode != 0:
        print(copy_result.stderr)
        sys.exit(1)

    # 4. Syntax check
    print(f"[{task_id}] Syntax check...")

    syntax = run(
        f"docker exec {container_name} "
        f"ansible-playbook --syntax-check /playbook.yml"
    )

    save_log("syntax_check.txt", syntax)

    if syntax.returncode != 0:
        print("Syntax check FAILED")
        append_result(None, {}, False, None)
        sys.exit(1)

    print("Syntax check PASSED")

    # 5. Task-specific setup
    print(f"[{task_id}] Applying task-specific setup...")

    setup_ok = setup_task()

    if not setup_ok:
        print("Task setup FAILED")
        sys.exit(1)

    # 6. Run #1
    print(f"[{task_id}] RUN #1...")

    run1 = run(
        f"docker exec {container_name} "
        f"ansible-playbook /playbook.yml"
    )

    save_log("run1.txt", run1)

    run1_stats = parse_recap(run1.stdout + run1.stderr)

    if run1.returncode != 0:
        print("RUN #1 FAILED")
        append_result(run1_stats, {}, True, None)
        sys.exit(1)

    # 7. Functional verification
    print(f"[{task_id}] Verifying intended state...")

    functional_correct = verify_task()

    if functional_correct is True:
        print("Functional verification: PASSED")
    elif functional_correct is False:
        print("Functional verification: FAILED")
    else:
        print("Functional verification: NOT YET DEFINED")

    # 8. Controlled drift injection for designated tasks.
    # P03 is intentionally modified after Run #1 / verification and before
    # Run #2. This is a controlled state-drift scenario.
    if task_id in DRIFT_INJECTION_TASKS:
        print(f"[{task_id}] Injecting environment drift before RUN #2...")

        drift_info = inject_curl_drift(container_name)

        print(
            f"[{task_id}] Drift injected: "
            f"{drift_info['before_version']} -> "
            f"{drift_info['injected_version']} now available"
        )

    # 9. Repeated executions: Runs #2 through #5
    repeat_stats = {}

    for run_number in range(2, 6):
        print(f"[{task_id}] RUN #{run_number}...")

        current_run = run(
            f"docker exec {container_name} "
            f"ansible-playbook /playbook.yml"
        )

        save_log(f"run{run_number}.txt", current_run)

        stats = parse_recap(
            current_run.stdout + current_run.stderr
        )

        repeat_stats[run_number] = stats

        if current_run.returncode != 0:
            print(f"RUN #{run_number} FAILED")
            break

    # 10. Final result
    print("")
    print("=== RESULT ===")
    print(f"Task: {task_id}")
    print(f"Model: {model}")
    print(f"Functional correct: {functional_correct}")
    print(
        f"Run 1 changed: "
        f"{run1_stats['changed'] if run1_stats else 'Unknown'}"
    )

    for r in range(2, 6):
        stats = repeat_stats.get(r)

        if stats:
            print(f"Run {r} changed: {stats['changed']}")
        else:
            print(f"Run {r} changed: NotRun")

    if functional_correct is not True:
        print("Repeated idempotent: N/A")
    else:
        repeated_idempotent = all(
            repeat_stats.get(r) is not None
            and repeat_stats[r]["failed"] == 0
            and repeat_stats[r]["changed"] == 0
            for r in range(2, 6)
        )

        if repeated_idempotent:
            print("Repeated idempotent: YES")
        else:
            print("Repeated idempotent: NO")

    append_result(
        run1_stats,
        repeat_stats,
        True,
        functional_correct
    )

    print(f"Evidence saved in: {log_dir}")
    print(f"Result saved in: {results_file}")

finally:
    print(f"[{task_id}] Removing container...")
    run(f"docker rm -f {container_name}")
