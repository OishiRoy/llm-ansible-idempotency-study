import pandas as pd

CSV_PATH = "results/Combined_Results/Idempotency_Rate/final_results.csv"

df = pd.read_csv(CSV_PATH)

df["model"] = df["model"].astype(str).str.strip()
df["functional_correct"] = (
    df["functional_correct"].astype(str).str.strip().str.upper()
)
df["structurally_idempotent"] = (
    df["structurally_idempotent"].astype(str).str.strip().str.upper()
)

summary_rows = []

print("MODEL-WISE IDEMPOTENCY RESULTS")
print("=" * 50)

for model in sorted(df["model"].dropna().unique()):
    m = df[df["model"] == model]

    total_generated = len(m)

    functional_correct = m[
        m["functional_correct"] == "YES"
    ]

    n_correct = len(functional_correct)

    n_idempotent = len(
        functional_correct[
            functional_correct["structurally_idempotent"] == "YES"
        ]
    )

    n_non_idempotent = len(
        functional_correct[
            functional_correct["structurally_idempotent"] == "NO"
        ]
    )

    n_fail = total_generated - n_correct

    ir = (
        n_idempotent / n_correct * 100
        if n_correct > 0
        else None
    )

    print(f"\n{model}")
    print(f"Total generated: {total_generated}")
    print(f"Functional correct: {n_correct}")
    print(f"Functional failures: {n_fail}")
    print(f"Idempotent: {n_idempotent}")
    print(f"Non-idempotent: {n_non_idempotent}")
    print(
        f"Idempotency Rate: {ir:.2f}%"
        if ir is not None
        else "Idempotency Rate: N/A"
    )

    summary_rows.append({
        "model": model,
        "total_generated": total_generated,
        "functional_correct": n_correct,
        "functional_failures": n_fail,
        "idempotent": n_idempotent,
        "non_idempotent": n_non_idempotent,
        "idempotency_rate_percent": round(ir, 2) if ir is not None else None,
    })

all_correct = df[
    df["functional_correct"] == "YES"
]

overall_total = len(df)
overall_correct = len(all_correct)

overall_idempotent = len(
    all_correct[
        all_correct["structurally_idempotent"] == "YES"
    ]
)

overall_non_idempotent = len(
    all_correct[
        all_correct["structurally_idempotent"] == "NO"
    ]
)

overall_fail = overall_total - overall_correct

overall_ir = (
    overall_idempotent / overall_correct * 100
    if overall_correct > 0
    else None
)

summary_rows.append({
    "model": "Overall",
    "total_generated": overall_total,
    "functional_correct": overall_correct,
    "functional_failures": overall_fail,
    "idempotent": overall_idempotent,
    "non_idempotent": overall_non_idempotent,
    "idempotency_rate_percent": (
        round(overall_ir, 2)
        if overall_ir is not None
        else None
    ),
})

summary = pd.DataFrame(summary_rows)

OUTPUT = "results/Combined_Results/Idempotency_Rate/idempotency_summary.csv"

summary.to_csv(OUTPUT, index=False)

print("\n" + "=" * 50)
print("OVERALL")
print(f"Total generated: {overall_total}")
print(f"Functional correct: {overall_correct}")
print(f"Functional failures: {overall_fail}")
print(f"Idempotent: {overall_idempotent}")
print(f"Non-idempotent: {overall_non_idempotent}")
print(
    f"Overall Idempotency Rate: {overall_ir:.2f}%"
    if overall_ir is not None
    else "Overall Idempotency Rate: N/A"
)

print(f"\nSaved: {OUTPUT}")
