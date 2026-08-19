"""Validates the parsed NIST data to ensure it meets the expected struture and length. Fails loudly and prints the exact problem if not."""

import json
from collections import Counter
from pathlib import Path


EXPECTED_COUNTS = { #Counted from the source document.
    "Govern": 19, 
    "Map": 18,
    "Measure": 22,
    "Manage": 13
}

def load(path: str) -> list[dict]:
    """Loads the parsed NIST JSONL file and returns a list of records"""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def validate(records: list[dict]) -> None:
    failures = []

    if len(records) != 72: #checks total number of records and ensures it is 72. 
        failures.append(f"Expected 72 records, found {len(records)}")

    counts = Counter(r["function"] for r in records)
    if dict(counts) != EXPECTED_COUNTS: #checks the number of records per function and ensures it matches the expected counts per function. 
        failures.append(f"Expected counts for this function is {EXPECTED_COUNTS}, found {dict(counts)}")

    ids = [r["chunk_id"] for r in records]
    duplicates = [i for i, n in Counter(ids).items() if n > 1] #checks for duplicate chunk_ids and ensures there are none.
    if duplicates:
        failures.append(f"Found duplicate chunk_ids: {duplicates}")

    for r in records: #individual record checks
        rid = r["display_id"]

        for field in ("text", "category_text", "category_id", "display_id"):
            if not r[field] or not r[field].strip(): #checks that the text, category_text, category_id and display_id fields are not empty or whitespace. 
                failures.append(f"Record {rid} has empty field {field}")

        if "<" in r["text"] or ">" in r["text"]: #checks that the text field does not contain any HTML tags. 
            failures.append(f"Record {rid} has HTML tags leaked in text")

        if r["text"][0].isdigit() or r["text"].startswith(":"): #checks that the text has been split correctly
            failures.append(f"Record {rid} text starts badly, split may have failed: {r['text'][:30]}")

        if not r["display_id"].startswith(r["function"]): #checks for function mismatch
            failures.append(f"Record {rid} has a function mismatch, got {r['function']}")

        if "  " in r["text"]: #checks that normalisation has been applied correctly and there are no double spaces in the text.
            failures.append(f"Record {rid} has double spaces in text, normalisation may have failed")

    if failures:
        print(f"Validation failed with {len(failures)} issues:\n")
        for f in failures:
            print(f"  {f}")
        raise SystemExit(1)

    print(f"Validation passed for {len(records)} records, counts {dict(counts)}")

if __name__ == "__main__":
    validate(load("corpus/parsed/nist.jsonl"))

#When checking the parsed data, it is suggested to run a reference spotcheck with the official NIST data document to ensure the statements has been parsed correctly. 
