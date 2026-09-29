"""
fix_results_csv.py

Cleans results.csv:
  1. Removes duplicate rows (keeps the LAST occurrence per task_id+model+condition,
     since later runs are assumed to be the more recent/authoritative attempt)
  2. Adds a new column `structurally_idempotent`, computed purely from
     run2_success + run2_changed -- independent of functional_correct.
  3. Fixes the old `idempotent` column so N/A vs No is applied consistently
     (kept as-is for backward compatibility, but recomputed with one rule
     instead of whatever ad-hoc logic produced the mixed N/A/No before).
  4. Leaves functional_correct untouched (including "NotChecked" -- that's
     a separate, honest signal that the verifier for that task isn't written yet).

Usage:
    python fix_results_csv.py results.csv results_clean.csv
"""
import csv
import sys


def to_bool_or_none(value):
    """'Yes' -> True, 'No' -> False, '' -> None"""
    v = (value or "").strip()
    if v == "Yes":
        return True
    if v == "No":
        return False
    return None


def compute_structurally_idempotent(row):
    """
    Idempotency in the classical sense: does a second, identical run of the
    SAME playbook change anything? This is intentionally blind to
    functional_correct -- a playbook can be wrong AND stable, or right AND
    stable, or wrong AND unstable, etc. Those are reported separately.
    """
    run2_success = to_bool_or_none(row.get("run2_success"))
    run2_changed = (row.get("run2_changed") or "").strip()

    if run2_success is not True:
        # run 2 itself failed/errored/was never attempted -> can't judge stability
        return "N/A"
    if run2_changed == "":
        return "N/A"
    try:
        changed_count = int(run2_changed)
    except ValueError:
        return "N/A"

    return "Yes" if changed_count == 0 else "No"


def compute_idempotent_legacy_consistent(row, structurally_idempotent):
    """
    Recreates the OLD 'idempotent' column but with one consistent rule
    (instead of the previous ad-hoc mix of No/N/A for the same situation).
    Old semantics appeared to mean: "fully correct AND stable".
    Kept only for backward-compatible reporting; do NOT use for analysis --
    use functional_correct + structurally_idempotent separately instead.
    """
    functional_correct = (row.get("functional_correct") or "").strip()

    if structurally_idempotent == "N/A":
        return "N/A"
    if functional_correct == "NotChecked":
        return "N/A"   # can't claim pass/fail on something never verified
    if functional_correct == "Yes" and structurally_idempotent == "Yes":
        return "Yes"
    return "No"


def dedupe_keep_last(rows):
    """Keep only the LAST row for each (task_id, model, condition) combo,
    preserving the overall order of first-appearance for readability."""
    key_to_row = {}
    key_order = []
    for row in rows:
        key = (row["task_id"], row["model"], row["condition"])
        if key not in key_to_row:
            key_order.append(key)
        key_to_row[key] = row  # overwritten each time -> last one wins
    return [key_to_row[k] for k in key_order]


def main(in_path, out_path):
    with open(in_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    original_count = len(rows)
    rows = dedupe_keep_last(rows)
    deduped_count = len(rows)

    for row in rows:
        structurally_idempotent = compute_structurally_idempotent(row)
        row["structurally_idempotent"] = structurally_idempotent
        row["idempotent"] = compute_idempotent_legacy_consistent(row, structurally_idempotent)

    fieldnames = list(rows[0].keys())
    if "idempotent" in fieldnames:
        fieldnames.remove("idempotent")
    if "structurally_idempotent" in fieldnames:
        fieldnames.remove("structurally_idempotent")
    fieldnames += ["structurally_idempotent", "idempotent"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Original rows: {original_count}")
    print(f"After de-dup (kept last per task_id+model+condition): {deduped_count}")
    print(f"Removed {original_count - deduped_count} duplicate rows.")
    print(f"Wrote cleaned file to: {out_path}")

    not_checked = sorted({r["task_id"] for r in rows if r.get("functional_correct") == "NotChecked"})
    if not_checked:
        print(f"\n[!] functional_correct is still 'NotChecked' for {len(not_checked)} tasks:")
        print("    " + ", ".join(not_checked))
        print("    Their `idempotent` value is now honestly 'N/A' instead of a misleading 'No'.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_results_csv.py <input.csv> <output.csv>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
