import subprocess
import sys
import re
import csv
from pathlib import Path

# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "drift"))

from task_rules import TASK_RULES
from drift_rules import DRIFT_RULES


# Usage:
# python scripts/drift/run_drift_experiment.py P02 GPT default

if len(sys.argv) != 4:
    print(
        "Usage: python scripts/drift/run_drift_experiment.py "
        "<TASK_ID> <MODEL> <CONDITION>"
    )
    sys.exit(1)

task_id = sys.argv[1]
model = sys.argv[2]
condition = sys.argv[3]

if task_id not in DRIFT_RULES:
    print(f"ERROR: No drift rule defined for {task_id}")
    sys.exit(1)

playbook = (
    PROJECT_ROOT
    / "generated"
    / model
    / condition
    / f"{task_id}.yml"
)

log_dir = (
    PROJECT_ROOT
    / "logs"
    / "Drift_Experiment"
    / model
    / condition
    / task_id
)

results_file = (
    PROJECT_ROOT
    / "results"
    / "Drift_Experiment"
    / "drift_results.csv"
)

if not playbook.exists():
    print(f"ERROR: Playbook not found: {playbook}")
    sys.exit(1)

log_dir.mkdir(parents=True, exist_ok=True)

container_name = (
    f"drift-{task_id.lower()}-{model.lower()}-{condition}"
).replace("_", "-")


def run(command):
    return subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True
    )


def docker_bash(command):
    return subprocess.run(
        [
            "docker",
            "exec",
            container_name,
            "bash",
            "-c",
            command
        ],
        text=True,
        capture_output=True
    )


def save_log(filename, result):
    path = log_dir / filename

    with open(path, "w") as f:
        f.write(result.stdout or "")
        f.write(result.stderr or "")


def parse_recap(text):
    match = re.search(
        r"ok=(\d+)\s+changed=(\d+)\s+"
        r"unreachable=(\d+)\s+failed=(\d+)",
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


def ansible_success(result, stats):
    return (
        result.returncode == 0
        and stats is not None
        and stats["failed"] == 0
        and stats["unreachable"] == 0
    )


def setup_task():
    rule = TASK_RULES.get(task_id)

    if not rule:
        return True

    setup_log = log_dir / "task_setup.txt"

    with open(setup_log, "w") as f:
        for command in rule.get("setup", []):
            result = docker_bash(command)

            f.write(f"$ {command}\n")
            f.write(result.stdout or "")
            f.write(result.stderr or "")
            f.write("\n")

            if result.returncode != 0:
                return False

    return True


def verify_command(command, filename):
    result = docker_bash(command)
    save_log(filename, result)
    return result.returncode == 0


def verify_initial_state():
    rule = TASK_RULES.get(task_id)

    if not rule:
        return None

    command = rule.get("verify")

    if not command:
        return None

    return verify_command(
        command,
        "initial_verification.txt"
    )


def inject_drift():
    rule = DRIFT_RULES[task_id]

    result = docker_bash(rule["inject"])
    save_log("drift_injection.txt", result)

    return result.returncode == 0


def verify_drift():
    command = DRIFT_RULES[task_id]["verify_drift"]

    return verify_command(
        command,
        "drift_verification.txt"
    )


def verify_recovery():
    command = DRIFT_RULES[task_id]["verify_recovery"]

    return verify_command(
        command,
        "recovery_verification.txt"
    )


def append_result(
    syntax_valid,
    initial_stats,
    initial_functional,
    drift_injected,
    drift_verified,
    recovery_stats,
    recovery_verified,
    post_stats
):
    results_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "task_id",
        "model",
        "condition",
        "category",
        "syntax_valid",
        "initial_run_success",
        "initial_run_changed",
        "initial_functional",
        "drift_injected",
        "drift_verified",
        "recovery_success",
        "recovery_changed",
        "recovery_verified",
        "post_recovery_success",
        "post_recovery_changed",
        "post_recovery_stable"
    ]

    initial_success = (
        initial_stats is not None
        and initial_stats["failed"] == 0
        and initial_stats["unreachable"] == 0
    )

    recovery_success = (
        recovery_stats is not None
        and recovery_stats["failed"] == 0
        and recovery_stats["unreachable"] == 0
    )

    post_success = (
        post_stats is not None
        and post_stats["failed"] == 0
        and post_stats["unreachable"] == 0
    )

    eligible_for_post = (
        initial_functional is True
        and drift_injected is True
        and drift_verified is True
        and recovery_success
        and recovery_verified is True
    )

    post_stable = (
        eligible_for_post
        and post_success
        and post_stats["changed"] == 0
    )

    row = {
        "task_id": task_id,
        "model": model,
        "condition": condition,
        "category": DRIFT_RULES[task_id]["category"],
        "syntax_valid": "Yes" if syntax_valid else "No",

        "initial_run_success": (
            "Yes" if initial_success else "No"
        ),

        "initial_run_changed": (
            initial_stats["changed"]
            if initial_stats
            else ""
        ),

        "initial_functional": (
            "Yes" if initial_functional is True
            else "No" if initial_functional is False
            else "NotChecked"
        ),

        "drift_injected": (
            "Yes" if drift_injected is True
            else "No" if drift_injected is False
            else "NotChecked"
        ),

        "drift_verified": (
            "Yes" if drift_verified is True
            else "No" if drift_verified is False
            else "NotChecked"
        ),

        "recovery_success": (
            "Yes" if recovery_success else "No"
        ),

        "recovery_changed": (
            recovery_stats["changed"]
            if recovery_stats
            else ""
        ),

        "recovery_verified": (
            "Yes" if recovery_verified is True
            else "No" if recovery_verified is False
            else "NotChecked"
        ),

        "post_recovery_success": (
            "Yes" if post_success else "No"
        ),

        "post_recovery_changed": (
            post_stats["changed"]
            if post_stats
            else ""
        ),

        "post_recovery_stable": (
            "Yes" if eligible_for_post and post_stable
            else "No" if eligible_for_post
            else "N/A"
        )
    }

    file_exists = results_file.exists()

    with open(results_file, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


# ---------------------------------------------------------
# Experiment
# ---------------------------------------------------------

syntax_valid = False
initial_stats = None
initial_functional = None
drift_injected = None
drift_verified = None
recovery_stats = None
recovery_verified = None
post_stats = None

print(
    f"[{task_id} | {model}] "
    "Creating fresh drift experiment container..."
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
    print("Container creation FAILED")
    print(create.stderr)
    sys.exit(1)

try:

    # 1. Container preparation
    print(f"[{task_id}] Preparing container...")

    prep = run(
        f"docker exec {container_name} "
        f"bash -c 'python3 --version && ansible --version'"
    )

    save_log("container_setup.txt", prep)

    if prep.returncode != 0:
        print("Container preparation FAILED")
        sys.exit(1)

    # 2. Copy playbook
    print(f"[{task_id}] Copying playbook...")

    copy_result = run(
        f'docker cp "{playbook}" '
        f'{container_name}:/playbook.yml'
    )

    if copy_result.returncode != 0:
        print("Playbook copy FAILED")
        print(copy_result.stderr)
        sys.exit(1)

    # 3. Syntax check
    print(f"[{task_id}] Syntax check...")

    syntax = run(
        f"docker exec {container_name} "
        f"ansible-playbook --syntax-check /playbook.yml"
    )

    save_log("syntax_check.txt", syntax)

    syntax_valid = syntax.returncode == 0

    if not syntax_valid:
        print("Syntax check FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print("Syntax check PASSED")

    # 4. Task-specific setup
    print(f"[{task_id}] Applying task-specific setup...")

    if not setup_task():
        print("Task setup FAILED")
        sys.exit(1)

    # 5. Initial execution
    print(f"[{task_id}] INITIAL RUN...")

    initial_run = run(
        f"docker exec {container_name} "
        f"ansible-playbook /playbook.yml"
    )

    save_log("initial_run.txt", initial_run)

    initial_stats = parse_recap(
        initial_run.stdout + initial_run.stderr
    )

    if not ansible_success(initial_run, initial_stats):
        print("INITIAL RUN FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print(
        f"Initial run changed: "
        f"{initial_stats['changed']}"
    )

    # 6. Initial functional verification
    print(f"[{task_id}] Verifying initial desired state...")

    initial_functional = verify_initial_state()

    if initial_functional is not True:
        print("Initial functional verification FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print("Initial functional verification PASSED")

    # 7. Inject controlled drift
    print(f"[{task_id}] Injecting controlled drift...")

    drift_injected = inject_drift()

    if not drift_injected:
        print("Drift injection FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print("Drift injection command PASSED")

    # 8. Verify drift
    print(f"[{task_id}] Verifying drift...")

    drift_verified = verify_drift()

    if not drift_verified:
        print("Drift verification FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print("Drift verification PASSED")

    # 9. Recovery execution
    print(f"[{task_id}] RECOVERY RUN...")

    recovery_run = run(
        f"docker exec {container_name} "
        f"ansible-playbook /playbook.yml"
    )

    save_log("recovery_run.txt", recovery_run)

    recovery_stats = parse_recap(
        recovery_run.stdout + recovery_run.stderr
    )

    if not ansible_success(
        recovery_run,
        recovery_stats
    ):
        print("Recovery run FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print(
        f"Recovery run changed: "
        f"{recovery_stats['changed']}"
    )

    # 10. Verify recovery
    print(f"[{task_id}] Verifying recovered state...")

    recovery_verified = verify_recovery()

    if not recovery_verified:
        print("Recovery verification FAILED")

        append_result(
            syntax_valid,
            initial_stats,
            initial_functional,
            drift_injected,
            drift_verified,
            recovery_stats,
            recovery_verified,
            post_stats
        )

        sys.exit(1)

    print("Recovery verification PASSED")

    # 11. Post-recovery stability execution
    print(f"[{task_id}] POST-RECOVERY RUN...")

    post_run = run(
        f"docker exec {container_name} "
        f"ansible-playbook /playbook.yml"
    )

    save_log("post_recovery_run.txt", post_run)

    post_stats = parse_recap(
        post_run.stdout + post_run.stderr
    )

    if not ansible_success(post_run, post_stats):
        print("Post-recovery run FAILED")
    else:
        print(
            f"Post-recovery changed: "
            f"{post_stats['changed']}"
        )

    # 12. Save result
    append_result(
        syntax_valid,
        initial_stats,
        initial_functional,
        drift_injected,
        drift_verified,
        recovery_stats,
        recovery_verified,
        post_stats
    )

    print("")
    print("=== DRIFT EXPERIMENT RESULT ===")
    print(f"Task: {task_id}")
    print(f"Model: {model}")
    print("Initial functional: PASS")
    print("Drift verified: PASS")
    print(
        f"Recovery changed: "
        f"{recovery_stats['changed']}"
    )
    print("Recovery verification: PASS")

    if (
        post_stats is not None
        and post_stats["failed"] == 0
        and post_stats["unreachable"] == 0
        and post_stats["changed"] == 0
    ):
        print("Post-recovery stable: YES")
    else:
        print("Post-recovery stable: NO")

    print(f"Evidence saved in: {log_dir}")
    print(f"Result saved in: {results_file}")

finally:
    print(f"[{task_id}] Removing container...")
    run(f"docker rm -f {container_name}")
