import csv
from pathlib import Path

models = ["GPT", "Claude", "Qwen"]

input_files = [
    Path(f"results/{model}/results_5runs.csv")
    for model in models
]

output_file = Path(
    "results/Combined_Results/results_5runs_combined.csv"
)

output_file.parent.mkdir(parents=True, exist_ok=True)

all_rows = []
fieldnames = None

for input_file in input_files:

    if not input_file.exists():
        print(f"ERROR: Missing file: {input_file}")
        raise SystemExit(1)

    with open(input_file, "r", newline="") as f:
        reader = csv.DictReader(f)

        if fieldnames is None:
            fieldnames = reader.fieldnames
        elif reader.fieldnames != fieldnames:
            print(f"ERROR: Columns do not match: {input_file}")
            raise SystemExit(1)

        all_rows.extend(reader)

with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )
    writer.writeheader()
    writer.writerows(all_rows)

print("Combined results created successfully.")
print(f"Total rows: {len(all_rows)}")
print(f"Saved to: {output_file}")