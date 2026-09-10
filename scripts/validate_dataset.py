"""Validate SyntHal records and aggregate-table structure using the standard library."""
from collections import Counter
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/00_dataset_SyntHal/SyntHal_prompts.jsonl"
FIELDS = {"dataset", "relation_key", "subject", "template", "prompt", "example_id"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines()]
    require(len(rows) == 3000, "Expected 3,000 records")
    for index, row in enumerate(rows):
        require(set(row) == FIELDS, f"Row {index}: unexpected fields")
        require(all(isinstance(v, str) and v for v in row.values()), f"Row {index}: invalid field value")
        require(row["dataset"] == "SyntHal", f"Row {index}: invalid dataset name")
        require(row["template"].count("{}") == 1, f"Row {index}: invalid template")
        require(row["prompt"] == row["template"].format(row["subject"]), f"Row {index}: incorrect prompt rendering")
    require(len({r["example_id"] for r in rows}) == 3000, "Example IDs must be unique")
    require(len({(r["relation_key"], r["subject"]) for r in rows}) == 3000, "Relation-subject pairs must be unique")
    counts = Counter(r["relation_key"] for r in rows)
    require(len(counts) == 15 and set(counts.values()) == {200}, "Expected 15 relations with 200 records each")
    with (ROOT / "docs/relation_inventory.csv").open(encoding="utf-8", newline="") as f:
        inventory = list(csv.DictReader(f))
    require(len(inventory) == 15, "Expected 15 relation-inventory entries")
    require({r["relation_key"] for r in inventory} == set(counts), "Relation-inventory mismatch")
    for item in inventory:
        group = [r for r in rows if r["relation_key"] == item["relation_key"]]
        require(int(item["records"]) == len(group), "Relation record-count mismatch")
        require({r["template"] for r in group} == {item["template"]}, "Relation-template mismatch")
    for stem in ("figure1", "figure2"):
        path = ROOT / f"data/01_main_results/source_tables/{stem}_points.csv"
        with path.open(encoding="utf-8", newline="") as f:
            points = list(csv.DictReader(f))
        require(len(points) == 60, f"{stem}: expected 60 model-relation rows")
        require(len({(r["model_key"], r["relation_key"]) for r in points}) == 60, f"{stem}: model-relation keys must be unique")
        require({r["relation_key"] for r in points} == set(counts), f"{stem}: relation mismatch")
    print("[PASS] 3,000 records; 15 relations with 200 records each")
    print("[PASS] 3,000 unique example IDs and relation-subject pairs")
    print("[PASS] Prompt rendering and relation inventory")
    print("[PASS] Figure 1 and Figure 2 aggregate-table structure")


def validate_aggregate_tables() -> None:
    from math import isclose, isfinite

    def table(path, expected_rows, expected_columns):
        with (ROOT / path).open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            require(len(reader.fieldnames) == expected_columns, f"{path}: unexpected column count")
        require(len(rows) == expected_rows, f"{path}: unexpected row count")
        require(all(None not in r and None not in r.values() for r in rows), f"{path}: malformed row")
        return rows

    def ratio(row, field, numerator, denominator):
        if denominator == 0:
            require(row[field] == "", f"{field}: zero denominator must have an empty value")
        else:
            value = float(row[field])
            require(isfinite(value) and isclose(value, numerator / denominator, rel_tol=1e-12, abs_tol=1e-12), f"{field}: inconsistent count/rate")

    base = "data/01_main_results/source_tables/"
    synthetic = table(base + "figure1_points.csv", 60, 15)
    for row in synthetic:
        hall, refusal, total = (int(row[c]) for c in ("n_hall", "n_refusal", "n_total"))
        require(min(hall, refusal) >= 0 and total == hall + refusal == 200, "Figure 1 counts do not sum to 200")
        ratio(row, "hall_rate", hall, total)
    natural = table(base + "appendix_natural_accuracy_points.csv", 112, 23)
    require(len({(r["model_key"], r["relation_key"]) for r in natural}) == 112, "Natural table has repeated keys")
    require(Counter(r["model_key"] for r in natural) == Counter({m: 28 for m in {r["model_key"] for r in synthetic}}), "Natural model coverage mismatch")
    require(len({r["relation_key"] for r in natural}) == 28, "Expected 28 natural relations")
    for row in natural:
        correct, hall, refusal, total, answered, noncorrect = (int(row[c]) for c in ("n_correct", "n_hall", "n_refusal", "n_total", "answered_n", "noncorrect_n"))
        require(min(correct, hall, refusal) >= 0 and total == correct + hall + refusal, "Natural counts do not sum to total")
        require(answered == correct + hall and noncorrect == hall + refusal, "Natural denominators disagree with counts")
        require(row["relation_group"] in {"factual", "commonsense", "linguistic", "bias"}, "Unknown relation group")
        ratio(row, "answered_accuracy", correct, answered)
        ratio(row, "hall_rate_answered", hall, answered)
        ratio(row, "hall_rate_noncorrect", hall, noncorrect)
    correlations = table("data/02_error_plausibility/plausibility_vs_linearity_correlations.csv", 5, 10)
    require(all(r["subset"] == "main_15_relations" for r in correlations), "Correlation subset mismatch")
    require(Counter(r["scope"] for r in correlations) == {"per_model": 4, "pooled_model_centered": 1}, "Unexpected correlation scopes")
    per_model = [r for r in correlations if r["scope"] == "per_model"]
    require({r["model_key"] for r in per_model} == {r["model_key"] for r in synthetic}, "Correlation models mismatch")
    require(all(int(r["n_rel"]) == 15 for r in per_model), "Expected 15 per-model relation points")
    pooled = next(r for r in correlations if r["scope"] == "pooled_model_centered")
    require(pooled["model_key"] == "ALL" and int(pooled["n_rel"]) == 60, "Expected 60 pooled model-relation points")
    print("[PASS] Compact table schemas, complete row counts, and correlation subsets")
    print("[PASS] Counts and rate denominators remain consistent")


if __name__ == "__main__":
    try:
        main()
        validate_aggregate_tables()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        sys.exit(1)
