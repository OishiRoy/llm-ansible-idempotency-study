from pathlib import Path
import pandas as pd
import yaml

# -------------------------------------------------
# Paths
# -------------------------------------------------
RESULTS_FILE = Path("results/Combined_Results/Idempotency_Rate/final_results.csv")
GENERATED_DIR = Path("generated")

DETAIL_OUTPUT = Path(
    "results/Combined_Results/Idempotency_Pattern_Analysis/pattern_analysis.csv"
)

SUMMARY_OUTPUT = Path(
    "results/Combined_Results/Idempotency_Pattern_Analysis/pattern_summary.csv"
)

MODEL_SUMMARY_OUTPUT = Path(
    "results/Combined_Results/Idempotency_Pattern_Analysis/pattern_summary_by_model.csv"
)

# -------------------------------------------------
# Module groups
# -------------------------------------------------
DECLARATIVE_MODULES = {
    "apt",
    "apt_repository",
    "package",
    "file",
    "copy",
    "template",
    "lineinfile",
    "blockinfile",
    "replace",
    "service",
    "systemd",
    "systemd_service",
    "user",
    "group",
    "cron",
    "get_url",
    "unarchive",
    "mount",
    "hostname",
    "timezone",
    "debconf",
}

FILE_CONFIG_MODULES = {
    "file",
    "copy",
    "template",
    "lineinfile",
    "blockinfile",
    "replace",
}

TASK_META_KEYS = {
    "name",
    "when",
    "notify",
    "register",
    "become",
    "become_user",
    "become_method",
    "tags",
    "vars",
    "environment",
    "ignore_errors",
    "changed_when",
    "failed_when",
    "check_mode",
    "delegate_to",
    "run_once",
    "loop",
    "with_items",
    "until",
    "retries",
    "delay",
    "args",
}

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def clean_module_name(name):
    """
    Convert:
      ansible.builtin.apt -> apt
      community.general.timezone -> timezone
    """
    return str(name).split(".")[-1]


def contains_key(obj, target_keys):
    """
    Recursively search YAML object for any target key.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if clean_module_name(key) in target_keys:
                return True
            if contains_key(value, target_keys):
                return True

    elif isinstance(obj, list):
        for item in obj:
            if contains_key(item, target_keys):
                return True

    return False


def collect_tasks(playbook):
    """
    Collect tasks, pre_tasks, post_tasks and handlers
    from all plays.
    """
    tasks = []
    handlers = []

    if not isinstance(playbook, list):
        return tasks, handlers

    for play in playbook:
        if not isinstance(play, dict):
            continue

        for section in ["pre_tasks", "tasks", "post_tasks"]:
            section_tasks = play.get(section, [])
            if isinstance(section_tasks, list):
                tasks.extend(section_tasks)

        section_handlers = play.get("handlers", [])
        if isinstance(section_handlers, list):
            handlers.extend(section_handlers)

    return tasks, handlers


def find_task_modules(task):
    """
    Detect modules used directly inside a task.
    """
    modules = set()

    if not isinstance(task, dict):
        return modules

    for key in task.keys():
        short_key = clean_module_name(key)

        if short_key in TASK_META_KEYS:
            continue

        # block/rescue/always are task structures, not modules
        if short_key in {"block", "rescue", "always"}:
            continue

        modules.add(short_key)

    # Recursively inspect block/rescue/always
    for section in ["block", "rescue", "always"]:
        nested = task.get(section)
        if isinstance(nested, list):
            for child in nested:
                modules.update(find_task_modules(child))

    return modules


def analyze_playbook(path):
    """
    Analyze one YAML playbook.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            playbook = yaml.safe_load(f)
    except Exception as e:
        return {
            "parse_success": "No",
            "parse_error": str(e),
        }

    tasks, handlers = collect_tasks(playbook)

    all_modules = set()
    has_when = False
    has_notify = False
    has_creates_removes = False
    has_explicit_state = False
    has_command_shell = False
    has_unguarded_command_shell = False

    for task in tasks:
        if not isinstance(task, dict):
            continue

        modules = find_task_modules(task)
        all_modules.update(modules)

        if "when" in task:
            has_when = True

        if "notify" in task:
            has_notify = True

        if contains_key(task, {"state"}):
            has_explicit_state = True

        if contains_key(task, {"creates", "removes"}):
            has_creates_removes = True

        command_in_task = bool(
            {"command", "shell"} & modules
        )

        if command_in_task:
            has_command_shell = True

            guarded_by_creates_removes = contains_key(
                task, {"creates", "removes"}
            )
            guarded_by_when = "when" in task

            if not (
                guarded_by_creates_removes
                or guarded_by_when
            ):
                has_unguarded_command_shell = True

    # Also inspect handlers for modules/state
    for handler in handlers:
        if isinstance(handler, dict):
            all_modules.update(find_task_modules(handler))

            if contains_key(handler, {"state"}):
                has_explicit_state = True

    has_declarative = bool(
        all_modules & DECLARATIVE_MODULES
    )

    has_file_config = bool(
        all_modules & FILE_CONFIG_MODULES
    )

    has_stat = "stat" in all_modules

    has_handlers = len(handlers) > 0 or has_notify

    return {
        "parse_success": "Yes",
        "parse_error": "",
        "modules_used": ";".join(sorted(all_modules)),
        "declarative_module": "Yes" if has_declarative else "No",
        "explicit_state": "Yes" if has_explicit_state else "No",
        "file_config_module": "Yes" if has_file_config else "No",
        "creates_removes_guard": "Yes" if has_creates_removes else "No",
        "when_condition": "Yes" if has_when else "No",
        "handler": "Yes" if has_handlers else "No",
        "stat_module": "Yes" if has_stat else "No",
        "shell_command": "Yes" if has_command_shell else "No",
        "unguarded_shell_command": (
            "Yes" if has_unguarded_command_shell else "No"
        ),
    }


# -------------------------------------------------
# Load final experiment results
# -------------------------------------------------
df = pd.read_csv(RESULTS_FILE)

for col in [
    "model",
    "condition",
    "task_id",
    "functional_correct",
    "structurally_idempotent",
]:
    df[col] = df[col].astype(str).str.strip()

df["functional_correct_norm"] = (
    df["functional_correct"].str.upper()
)

df["idempotent_norm"] = (
    df["structurally_idempotent"].str.upper()
)

# -------------------------------------------------
# RQ2 population:
# only functionally correct + idempotent playbooks
# -------------------------------------------------
rq2_df = df[
    (df["functional_correct_norm"] == "YES")
    & (df["idempotent_norm"] == "YES")
].copy()

print("=" * 60)
print("RQ2 IMPLEMENTATION PATTERN ANALYSIS")
print("=" * 60)
print(
    f"Functionally correct + idempotent playbooks: "
    f"{len(rq2_df)}"
)

# -------------------------------------------------
# Analyze YAML files
# -------------------------------------------------
rows = []

for _, row in rq2_df.iterrows():
    model = row["model"]
    condition = row["condition"]
    task_id = row["task_id"]

    yaml_path = (
        GENERATED_DIR
        / model
        / condition
        / f"{task_id}.yml"
    )

    base = {
        "task_id": task_id,
        "model": model,
        "condition": condition,
        "yaml_path": str(yaml_path),
    }

    if not yaml_path.exists():
        base.update({
            "parse_success": "No",
            "parse_error": "YAML file not found",
        })
        rows.append(base)
        print(f"[MISSING] {yaml_path}")
        continue

    analysis = analyze_playbook(yaml_path)
    base.update(analysis)
    rows.append(base)

detail_df = pd.DataFrame(rows)

# -------------------------------------------------
# Save detailed per-playbook results
# -------------------------------------------------
detail_df.to_csv(DETAIL_OUTPUT, index=False)

# Only successfully parsed files for percentages
valid_df = detail_df[
    detail_df["parse_success"] == "Yes"
].copy()

pattern_columns = {
    "Declarative module": "declarative_module",
    "Explicit state": "explicit_state",
    "File/config module": "file_config_module",
    "Creates/removes guard": "creates_removes_guard",
    "When condition": "when_condition",
    "Handler": "handler",
    "Stat module": "stat_module",
    "Shell/command": "shell_command",
    "Unguarded shell/command": "unguarded_shell_command",
}

# -------------------------------------------------
# Overall pattern summary
# -------------------------------------------------
summary_rows = []
total_valid = len(valid_df)

for pattern_name, column in pattern_columns.items():
    count = (
        valid_df[column]
        .astype(str)
        .str.upper()
        .eq("YES")
        .sum()
    )

    percentage = (
        count / total_valid * 100
        if total_valid > 0
        else 0
    )

    summary_rows.append({
        "pattern": pattern_name,
        "playbooks_using_pattern": int(count),
        "total_idempotent_playbooks": total_valid,
        "percentage": round(percentage, 2),
    })

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(SUMMARY_OUTPUT, index=False)

# -------------------------------------------------
# Model-wise pattern summary
# Useful later for RQ3
# -------------------------------------------------
model_summary_rows = []

for model in sorted(valid_df["model"].unique()):
    model_df = valid_df[
        valid_df["model"] == model
    ]

    model_total = len(model_df)

    for pattern_name, column in pattern_columns.items():
        count = (
            model_df[column]
            .astype(str)
            .str.upper()
            .eq("YES")
            .sum()
        )

        percentage = (
            count / model_total * 100
            if model_total > 0
            else 0
        )

        model_summary_rows.append({
            "model": model,
            "pattern": pattern_name,
            "count": int(count),
            "total_idempotent_playbooks": model_total,
            "percentage": round(percentage, 2),
        })

model_summary_df = pd.DataFrame(
    model_summary_rows
)

model_summary_df.to_csv(
    MODEL_SUMMARY_OUTPUT,
    index=False
)

# -------------------------------------------------
# Print result
# -------------------------------------------------
print("\nOVERALL PATTERN SUMMARY")
print("-" * 60)

for _, row in summary_df.iterrows():
    print(
        f"{row['pattern']:<28} "
        f"{int(row['playbooks_using_pattern']):>2}/"
        f"{int(row['total_idempotent_playbooks'])}"
        f" = {row['percentage']:.2f}%"
    )

print("\nSaved files:")
print(f"1. {DETAIL_OUTPUT}")
print(f"2. {SUMMARY_OUTPUT}")
print(f"3. {MODEL_SUMMARY_OUTPUT}")
