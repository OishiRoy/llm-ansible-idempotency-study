import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Input and output paths
input_file = Path(
    "results/Analysis/Implementation_Patterns/implementation_patterns.csv"
)
output_dir = Path("figures/RQ2")
output_dir.mkdir(parents=True, exist_ok=True)

# Read RQ2 analysis results
df = pd.read_csv(input_file)

# RQ2 concerns idempotency outcomes, so patterns with no eligible
# playbooks are excluded from the outcome plot.
df = df[df["Eligible_Usages"] > 0].copy()

# Sort by number of eligible playbooks
df = df.sort_values("Eligible_Usages", ascending=True)

# Make labels easier to read
df["Pattern_Label"] = (
    df["Pattern"]
    .str.replace("_", " ", regex=False)
)

# Create figure
fig, ax = plt.subplots(figsize=(7.2, 5.6))

# Idempotent portion
ax.barh(
    df["Pattern_Label"],
    df["Idempotent_Usages"],
    label="Idempotent"
)

# Non-idempotent portion
ax.barh(
    df["Pattern_Label"],
    df["Non_Idempotent_Usages"],
    left=df["Idempotent_Usages"],
    label="Non-idempotent"
)

# Add counts to the end of each bar
for i, row in enumerate(df.itertuples()):
    eligible = row.Eligible_Usages
    idem = row.Idempotent_Usages
    non_idem = row.Non_Idempotent_Usages

    if non_idem > 0:
        label = f"{idem} + {non_idem}"
    else:
        label = f"{idem}"

    ax.text(
        eligible + 0.25,
        i,
        label,
        va="center",
        fontsize=8
    )

ax.set_xlabel("Number of eligible playbooks")
ax.set_ylabel("Implementation pattern")

ax.legend(
    loc="lower right",
    frameon=True
)

ax.grid(
    axis="x",
    linestyle="--",
    alpha=0.35
)

ax.set_axisbelow(True)

# Give labels on the right some space
ax.set_xlim(0, df["Eligible_Usages"].max() + 4)

plt.tight_layout()

# Save publication-quality versions
plt.savefig(
    output_dir / "rq2_implementation_patterns.pdf",
    bbox_inches="tight"
)

plt.savefig(
    output_dir / "rq2_implementation_patterns.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("RQ2 figure created successfully.")
print("PDF: figures/rq2_implementation_patterns.pdf")
print("PNG: figures/rq2_implementation_patterns.png")
