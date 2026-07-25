import csv
from pathlib import Path

IN_RAW = "data/books_metadata_raw.csv"
IN_ENRICHED = "data/books_metadata_enriched.csv"

def main():
    raw_path = Path(IN_RAW)
    enriched_path = Path(IN_ENRICHED)

    if not raw_path.exists():
        print(f"Error: {raw_path} does not exist.")
        return

    # Read existing enriched rows and keep track of their IDs
    existing_ids = set()
    enriched_rows = []
    
    if enriched_path.exists():
        with open(enriched_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                existing_ids.add(row["id"])
                enriched_rows.append(row)
        print(f"Loaded {len(enriched_rows)} existing rows from {enriched_path}")
    else:
        # If enriched file doesn't exist, we start from scratch
        print(f"{enriched_path} does not exist. Creating a new one.")
        # Field names should match raw + 'ai_filled'
        with open(raw_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames) + ["ai_filled"]

    # Read raw rows and append new ones
    new_count = 0
    with open(raw_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] not in existing_ids:
                # Add the 'ai_filled' field with empty value
                row["ai_filled"] = ""
                enriched_rows.append(row)
                existing_ids.add(row["id"])
                new_count += 1

    print(f"Adding {new_count} new rows from {raw_path}")

    # Ensure fieldnames has 'ai_filled'
    if "ai_filled" not in fieldnames:
        fieldnames.append("ai_filled")

    # Write all rows back to enriched file
    with open(enriched_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    print(f"Saved total {len(enriched_rows)} rows to {enriched_path}")

if __name__ == "__main__":
    main()
