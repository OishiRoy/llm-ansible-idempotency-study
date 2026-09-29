import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --------------------------------------------------
# Paths
# --------------------------------------------------

input_file = Path(
    "results/Analysis/Model_Category_Comparison/"
    "model_category_comparison.csv"
)

output_dir = Path("figures/RQ3")
output_dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Read data
# --------------------------------------------------

df = pd.read_csv(input_file)

models = ["GPT", "Claude", "Qwen"]

categories = [
    "Package Management",
    "File & Directory Management",
    "User & Permission Management",
    "Service Management",
    "System & Environment Management",
    "Configuration & Scheduled Tasks"
]

category_labels = [
    "Package",
    "File & Directory",
    "User & Permission",
    "Service",
    "System & Environment",
    "Configuration & Scheduled"
]

markers = {
    "GPT": "o",
    "Claude": "s",
    "Qwen": "^"
}

colors = {
    "GPT": "tab:blue",
    "Claude": "tab:orange",
    "Qwen": "tab:green"
}
# --------------------------------------------------
# Create figure
# --------------------------------------------------

fig, axes = plt.subplots(
    1, 3,
    figsize=(7.2, 3.5),
    sharey=True
)

y = np.arange(len(categories))

for index, (ax, model) in enumerate(zip(axes, models)):

    rates = []
    counts = []

    for category in categories:

        row = df[
            (df["Model"] == model) &
            (df["Category"] == category)
        ]

        if len(row) != 1:
            raise ValueError(
                f"Expected one row for {model} / {category}, "
                f"found {len(row)}."
            )

        row = row.iloc[0]

        rate = float(row["Idempotency_Rate_Percent"])
        idem = int(row["Repeatedly_Idempotent"])
        eligible = int(row["Eligible"])

        rates.append(rate)
        counts.append(f"{idem}/{eligible}")

    # --------------------------------------------------
    # 100% reference line
    # --------------------------------------------------

    ax.axvline(
    100,
    linestyle="--",
    linewidth=0.9,
    color=colors[model],
    alpha=0.60,
    zorder=1
)

    # --------------------------------------------------
    # Draw deviation only when rate < 100
    # --------------------------------------------------

    for yi, rate in zip(y, rates):

        if rate < 100:
            ax.hlines(
              yi,
              xmin=rate,
              xmax=100,
              linewidth=1.4,
              color=colors[model],
              zorder=2
            )
    # --------------------------------------------------
    # Points
    # --------------------------------------------------

    ax.scatter(
    rates,
    y,
    marker=markers[model],
    s=48,
    color=colors[model],
    zorder=3
    )

    # --------------------------------------------------
    # Important annotations only
    # --------------------------------------------------

    for yi, rate, count in zip(y, rates, counts):

        # Non-100% result
        if rate < 100:
            ax.annotate(
                f"{rate:.0f}% ({count})",
                xy=(rate, yi),
                xytext=(5, -13),
                textcoords="offset points",
                ha="left",
                va="bottom",
                fontsize=7.5,
                fontweight="bold"
            )

        # Reduced denominator but still 100%
        elif count != "5/5":
            ax.annotate(
                f"{count}",
                xy=(rate, yi),
                xytext=(-6, -13),
                textcoords="offset points",
                ha="right",
                va="bottom",
                fontsize=7
            )

    # --------------------------------------------------
    # Panel formatting
    # --------------------------------------------------

    ax.set_title(
        model,
        fontsize=10,
        fontweight="bold",
        pad=7
    )

    ax.set_xlim(75, 103)

    ax.set_xticks(
        [80, 85, 90, 95, 100]
    )

    ax.tick_params(
        axis="x",
        labelsize=7
    )

    ax.grid(
        axis="x",
        linestyle="--",
        linewidth=0.5,
        alpha=0.25
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Hide left spine except first panel
    if index > 0:
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)

# --------------------------------------------------
# Shared category labels
# --------------------------------------------------

axes[0].set_yticks(y)
axes[0].set_yticklabels(
    category_labels,
    fontsize=7.5
)

axes[0].invert_yaxis()

fig.supxlabel(
    "Idempotency Rate (%)",
    fontsize=8.5,
    y=0.02
)

plt.tight_layout(rect=[0, 0.05, 1, 1])

# --------------------------------------------------
# Save
# --------------------------------------------------

plt.savefig(
    output_dir / "rq3_model_category_deviation.pdf",
    bbox_inches="tight"
)

plt.savefig(
    output_dir / "rq3_model_category_deviation.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("RQ3 deviation figure created successfully.")
print(
    "PDF: figures/RQ3/"
    "rq3_model_category_deviation.pdf"
)
print(
    "PNG: figures/RQ3/"
    "rq3_model_category_deviation.png"
)