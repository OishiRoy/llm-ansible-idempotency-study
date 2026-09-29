import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --------------------------------------------------
# Paths
# --------------------------------------------------

input_file = Path(
    "results/reported_results/drift_results.csv"
)

output_dir = Path("figures/RQ4")
output_dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Read data
# --------------------------------------------------

df = pd.read_csv(input_file)

tasks = [
    "P02", "P08", "P09", "P14",
    "P15", "P19", "P21", "P24",
    "P27", "P28", "P29", "P30"
]

models = ["GPT", "Claude", "Qwen"]

markers = {
    "GPT": "o",
    "Claude": "s",
    "Qwen": "^"
}

linestyles = {
    "GPT": "-",
    "Claude": "--",
    "Qwen": ":"
}

# Small offsets make overlapping points visible
offsets = {
    "GPT": -0.08,
    "Claude": 0.00,
    "Qwen": 0.08
}

x = np.arange(len(tasks))

# --------------------------------------------------
# Figure
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(7.2, 3.2))

for model in models:

    values = []

    for task in tasks:

        row = df[
            (df["task_id"] == task) &
            (df["model"] == model)
        ]

        if len(row) != 1:
            raise ValueError(
                f"Expected one result for {model}-{task}, "
                f"found {len(row)}."
            )

        values.append(
            int(row.iloc[0]["recovery_changed"])
        )

    ax.plot(
        x + offsets[model],
        values,
        marker=markers[model],
        linestyle=linestyles[model],
        linewidth=1.2,
        markersize=6,
        label=model
    )

# --------------------------------------------------
# Post-recovery baseline
# --------------------------------------------------

ax.axhline(
    y=0,
    linestyle="--",
    linewidth=1.0
)

ax.annotate(
    "Post-recovery: 0 changes in all 36 cases",
    xy=(9.2, 0),
    xytext=(6.8, 0.38),
    arrowprops=dict(
        arrowstyle="->",
        linewidth=0.8
    ),
    fontsize=7.5
)

# --------------------------------------------------
# Highlight meaningful recovery differences
# --------------------------------------------------

ax.annotate(
    "2 changes",
    xy=(5, 2),
    xytext=(4.25, 2.25),
    arrowprops=dict(
        arrowstyle="->",
        linewidth=0.7
    ),
    fontsize=7.5
)

# Claude P27 only
claude_p27_x = 8 + offsets["Claude"]

ax.annotate(
    "Claude: 2",
    xy=(claude_p27_x, 2),
    xytext=(7.35, 2.25),
    arrowprops=dict(
        arrowstyle="->",
        linewidth=0.7
    ),
    fontsize=7.5
)

# --------------------------------------------------
# Axes
# --------------------------------------------------

ax.set_xticks(x)
ax.set_xticklabels(tasks, fontsize=8)

ax.set_yticks([0, 1, 2])
ax.set_ylim(-0.15, 2.5)

ax.set_xlabel(
    "Perturbation Task",
    fontsize=9
)

ax.set_ylabel(
    "Reported Changes During Recovery",
    fontsize=9
)

ax.tick_params(
    axis="y",
    labelsize=8
)

# --------------------------------------------------
# Grid / legend
# --------------------------------------------------

ax.grid(
    axis="y",
    linestyle="--",
    linewidth=0.5,
    alpha=0.3
)

ax.set_axisbelow(True)

ax.legend(
    loc="lower center",
    bbox_to_anchor=(0.5, 1.01),
    ncol=3,
    frameon=False,
    fontsize=8
)

# --------------------------------------------------
# Clean appearance
# --------------------------------------------------

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

# --------------------------------------------------
# Save
# --------------------------------------------------

plt.savefig(
    output_dir / "rq4_recovery_behavior.pdf",
    bbox_inches="tight"
)

plt.savefig(
    output_dir / "rq4_recovery_behavior.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("RQ4 figure created successfully.")
print("PDF: figures/RQ4/rq4_recovery_behavior.pdf")
print("PNG: figures/RQ4/rq4_recovery_behavior.png")