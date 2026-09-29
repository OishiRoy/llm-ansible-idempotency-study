import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --------------------------------------------------
# Final experimental results
# --------------------------------------------------

models = ["GPT", "Claude", "Qwen", "Overall"]

fcr = [100.00, 96.67, 96.67, 97.78]
ir  = [100.00, 96.55, 100.00, 98.86]

fcr_counts = ["30/30", "29/30", "29/30", "88/90"]
ir_counts  = ["30/30", "28/29", "29/29", "87/88"]

# Model-wise colors
colors = [
    "tab:blue",
    "tab:green",
    "tab:red",
    "tab:purple"
]

# --------------------------------------------------
# Positions
# --------------------------------------------------

group_centers = np.arange(len(models)) * 2.4

bar_width = 0.65

fcr_x = group_centers - 0.38
ir_x  = group_centers + 0.38

# --------------------------------------------------
# Figure
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(7.2, 3.4))

for i, model in enumerate(models):

    # FCR
    ax.bar(
        fcr_x[i],
        fcr[i],
        width=bar_width,
        color=colors[i],
        edgecolor="black",
        linewidth=0.6
    )

    # IR
    ax.bar(
        ir_x[i],
        ir[i],
        width=bar_width,
        color=colors[i],
        edgecolor="black",
        linewidth=0.6
    )

    # Percentage labels
    ax.text(
        fcr_x[i],
        fcr[i] + 1.3,
        f"{fcr[i]:.1f}%",
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold"
    )

    ax.text(
        ir_x[i],
        ir[i] + 1.3,
        f"{ir[i]:.1f}%",
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold"
    )

    # Count labels inside bars
    ax.text(
        fcr_x[i],
        4,
        fcr_counts[i],
        ha="center",
        va="center",
        fontsize=7.5,
        color="white",
        fontweight="bold"
    )

    ax.text(
        ir_x[i],
        4,
        ir_counts[i],
        ha="center",
        va="center",
        fontsize=7.5,
        color="white",
        fontweight="bold"
    )

# --------------------------------------------------
# FCR / IR labels below individual bars
# --------------------------------------------------

bar_positions = []
bar_labels = []

for i in range(len(models)):
    bar_positions.extend([fcr_x[i], ir_x[i]])
    bar_labels.extend(["FCR", "IR"])

ax.set_xticks(bar_positions)
ax.set_xticklabels(
    bar_labels,
    fontsize=8
)

# Model names below each pair
for i, model in enumerate(models):

    ax.text(
        group_centers[i],
        -11,
        model,
        ha="center",
        va="top",
        fontsize=9,
        fontweight="bold",
        clip_on=False
    )

# --------------------------------------------------
# Axis
# --------------------------------------------------

ax.set_ylabel(
    "Rate (%)",
    fontsize=9
)

# Important: percentage axis starts at zero
ax.set_ylim(0, 108)

ax.set_yticks(
    np.arange(0, 101, 20)
)

ax.tick_params(
    axis="y",
    labelsize=8
)

# --------------------------------------------------
# Grid
# --------------------------------------------------

ax.grid(
    axis="y",
    linestyle="--",
    linewidth=0.5,
    alpha=0.30
)

ax.set_axisbelow(True)

# --------------------------------------------------
# Clean publication style
# --------------------------------------------------

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# No legend needed:
# model names + model-specific colors already identify groups.

plt.subplots_adjust(bottom=0.20)
plt.tight_layout()

# --------------------------------------------------
# Output
# --------------------------------------------------

output_dir = Path("figures/RQ1")
output_dir.mkdir(parents=True, exist_ok=True)

plt.savefig(
    output_dir / "rq1_fcr_ir_grouped.pdf",
    bbox_inches="tight"
)

plt.savefig(
    output_dir / "rq1_fcr_ir_grouped.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("RQ1 grouped bar figure created successfully.")
print("PDF: figures/RQ1/rq1_fcr_ir_grouped.pdf")
print("PNG: figures/RQ1/rq1_fcr_ir_grouped.png")