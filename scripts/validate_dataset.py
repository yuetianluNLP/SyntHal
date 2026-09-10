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


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        sys.exit(1)
