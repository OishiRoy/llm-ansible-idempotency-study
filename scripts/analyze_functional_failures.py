import pandas as pd
from pathlib import Path

INPUT = Path("results/Combined_Results/Idempotency_Rate/final_results.csv")
OUTDIR = Path("results/Combined_Results/Functional_Failure_Analysis")
OUTDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# All cases that did not achieve verified functional success
failed = df[
    df["functional_correct"].astype(str).str.strip().str.upper() != "YES"
].copy()

# Evidence-based classification of the latest non-success cases
classification = {
    ("Claude", "P22"): (
        "Run1",
        "Generated task-specification mismatch",
        "Model output mismatch",
        "Generated playbook implemented a cron task instead of changing "
        "Nginx worker_connections from 768 to 1024"
    ),

    ("Qwen", "P01"): (
        "Run1",
        "Mixed implementation/environment issue",
        "Mixed attribution",
        "The playbook correctly installed Nginx but additionally attempted "
        "to start and enable the service using systemd; systemctl was not "
        "available in the container environment"
    ),
}

rows = []

for _, row in failed.iterrows():
    key = (row["model"], row["task_id"])

    stage, cause, attribution, evidence = classification.get(
        key,
        ("Unclassified", "Unclassified", "Unclassified", "")
    )

    rows.append({
        "task_id": row["task_id"],
        "model": row["model"],
        "syntax_valid": row["syntax_valid"],
        "run1_success": row["run1_success"],
        "functional_correct": row["functional_correct"],
        "failure_stage": stage,
        "cause_category": cause,
        "attribution": attribution,
        "evidence": evidence,
    })

failure_cases = pd.DataFrame(rows)

failure_cases.to_csv(
    OUTDIR / "failure_cases.csv",
    index=False
)

# Cause summary
cause_summary = (
    failure_cases.groupby("cause_category")
    .size()
    .reset_index(name="count")
)

cause_summary["percentage"] = (
    cause_summary["count"] / len(failure_cases) * 100
).round(2)

cause_summary = cause_summary.sort_values(
    ["count", "cause_category"],
    ascending=[False, True]
)

cause_summary.to_csv(
    OUTDIR / "failure_cause_summary.csv",
    index=False
)

# Functional correctness vs idempotency
summary = []

for model in ["GPT", "Claude", "Qwen"]:
    sub = df[df["model"] == model]

    total = len(sub)
    fc = sub["functional_correct"].astype(str).str.upper().eq("YES").sum()
    idem = sub["structurally_idempotent"].astype(str).str.upper().eq("YES").sum()

    summary.append({
        "model": model,
        "total_generated": total,
        "functional_correct": fc,
        "functional_success_rate_percent": round(fc / total * 100, 2),
        "idempotent": idem,
        "idempotency_rate_percent": round(idem / fc * 100, 2) if fc else 0
    })

total = len(df)
fc = df["functional_correct"].astype(str).str.upper().eq("YES").sum()
idem = df["structurally_idempotent"].astype(str).str.upper().eq("YES").sum()

summary.append({
    "model": "Overall",
    "total_generated": total,
    "functional_correct": fc,
    "functional_success_rate_percent": round(fc / total * 100, 2),
    "idempotent": idem,
    "idempotency_rate_percent": round(idem / fc * 100, 2) if fc else 0
})

correctness = pd.DataFrame(summary)

correctness.to_csv(
    OUTDIR / "correctness_vs_idempotency.csv",
    index=False
)

print("=" * 70)
print("RQ4 FUNCTIONAL FAILURE ANALYSIS")
print("=" * 70)
print(f"Cases analyzed: {len(failure_cases)}")

print("\nFAILURE CAUSE SUMMARY")
print("-" * 70)
print(cause_summary.to_string(index=False))

print("\nCORRECTNESS VS IDEMPOTENCY")
print("-" * 70)
print(correctness.to_string(index=False))

print("\nSaved files:")
print("1.", OUTDIR / "failure_cases.csv")
print("2.", OUTDIR / "failure_cause_summary.csv")
print("3.", OUTDIR / "correctness_vs_idempotency.csv")