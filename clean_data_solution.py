"""
clean_data_solution.py

Cleans the raw, messy raw_transactions.csv export and produces a cleaned,
standardised set of transactions.

Pipeline:
  1. Load the raw CSV
  2. Drop rows with a missing/blank description or amount (unrecoverable)
  3. Normalize formatting: standardise amount to a plain number, clean up
     whitespace/casing in the description
  4. Drop exact duplicate rows
  5. Filter out out-of-scope junk rows (not real transactions)
"""

import csv
import json

INPUT_PATH = "./raw_transactions.csv"
OUTPUT_PATH = "./cleaned_transactions.jsonl"

# Out-of-scope junk rows that aren't real transactions and should be dropped.
JUNK_DESCRIPTIONS = {
    "OPENING BALANCE", "INTEREST CHARGED", "ACCOUNT MAINTENANCE FEE ADJUSTMENT",
    "STATEMENT CARRIED FORWARD", "BALANCE BROUGHT FORWARD",
}


def normalize_description(raw_desc):
    """Trim stray whitespace, collapse repeated spaces, uppercase."""
    return " ".join(raw_desc.split()).upper()


def normalize_amount(raw_amount):
    """
    The only messy amount format in this dataset is a dollar sign, e.g.
    "$45.90" or "-$45.90". Strip the "$" and convert to a number. Returns
    None if it can't be parsed at all, used to drop unrecoverable rows.
    """
    text = raw_amount.strip().replace("$", "")
    try:
        return float(text)
    except ValueError:
        return None


def clean(input_path, output_path):
    seen = set()
    kept = []
    stats = {"total": 0, "duplicate": 0, "missing_field": 0, "junk": 0, "kept": 0}

    with open(input_path, newline="") as f:
        for row in csv.DictReader(f):
            stats["total"] += 1
            raw_desc, raw_amount = row["description"], row["amount"]

            # Drop rows missing a description or amount.
            if not raw_desc.strip() or raw_desc.strip() in ("POS", "SQ *") or not raw_amount.strip():
                stats["missing_field"] += 1
                continue

            description = normalize_description(raw_desc)
            amount = normalize_amount(raw_amount)
            if amount is None:
                stats["missing_field"] += 1
                continue

            # Drop exact duplicates (same cleaned description + amount).
            dedupe_key = (description, amount)
            if dedupe_key in seen:
                stats["duplicate"] += 1
                continue
            seen.add(dedupe_key)

            # Drop out-of-scope junk rows.
            if description in JUNK_DESCRIPTIONS:
                stats["junk"] += 1
                continue

            kept.append({"description": description, "amount": amount})
            stats["kept"] += 1

    with open(output_path, "w") as f:
        for row in kept:
            f.write(json.dumps(row) + "\n")

    return stats


if __name__ == "__main__":
    stats = clean(INPUT_PATH, OUTPUT_PATH)
    print("Cleaning summary:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
