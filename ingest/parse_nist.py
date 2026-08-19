"""Parses the NIST data file and returns structured records in a JSON format """

from lxml import html
import json
from pathlib import Path

#define constants for the NIST data
FUNCTIONS = ["Govern", "Map", "Measure", "Manage"]
SOURCE_URL = "https://airc.nist.gov/airmf-resources/airmf/5-sec-core/"
RETRIEVED = "2026-08-18"
OUTPUT_PATH = Path("corpus/parsed/nist.jsonl")

def normalise(text: str) -> str:
    """Normalises NIST text by collapsing whitespace (not only stripping) to single spaces and trimming leading/trailing whitespace"""
    return " ".join(text.split())

def split_id(text: str) -> str:
    """Splits 'Govern 1.1: ... ' into ('Govern 1.1', '...')"""
    if ":" not in text: #important to guard against this in case data is malformed 
        raise ValueError(f"No colon found in cell text: {text[:60]}")
    id , content = text.split(":", 1)
    return normalise(id), normalise(content)

def canonical_id(display_id: str) -> str:
    """Converts 'Govern 1.1' to 'nist:govern-1.1'"""
    return "nist:" + display_id.lower().replace(" ", "-")

def parse_nist(input_file: str) -> list[dict]:
    """Parses the NIST data file and returns structured records in a JSON format"""
    doc = html.parse(input_file).getroot()
    tables = doc.xpath("//table")

    if len(tables) != 4:
        raise ValueError(f"Expected 4 tables, found {len(tables)}") #Because we expect 4 tables in the NIST data file.

    records = []

    for function, table in zip(FUNCTIONS, tables): # we use zip to iterate over both functions and tables simultaneously.
        current_category_id = 0
        current_category_text = None

        for row in table.xpath(".//tr"):
            cells = row.xpath("./th") #as from inspection we realised all cell values were in th tags, not td tags.

            if not cells: #check if the row has no cells. 
                continue

            if normalise(cells[0].text_content()) == "Categories":
                continue

            if len(cells) == 2: #means it is the row with both category and subcategory with the content(very first row)
                current_category_id, current_category_text = split_id(
                    cells[0].text_content()
                )
                sub_cell = cells[1]
            else: #means its the rows below, with only the subcategory and content
                sub_cell = cells[0]

            display_id, statement = split_id(sub_cell.text_content())

            records.append({
                "chunk_id": canonical_id(display_id), #machine key. lowercaed, hyphenated and name spaced to make matching robust. 
                "display_id": display_id, #faithful record of what NIST prints, job is fidelity. 
                "document": "NIST AI RMF 1.0",
                "function": function,
                "category_id": current_category_id,
                "category_text": current_category_text,
                "text": statement,
                "embed_text": f"{current_category_id}: {current_category_text} | {display_id}: {statement}",
                "scored": True,
                "source_url": SOURCE_URL,
                "retrieved": RETRIEVED,
            })
            #defined schema that we have chosen for the parsing of the NIST data. 

    return records

def write_jsonl(records: list[dict], path: Path) -> None: #JSONL over JSON as JSON Lines is one complete JSON object per line, so you can stream it line by line without loading the whole file into memory. grep it and gte back a complete record rather than a fragment and git diffs it sensibly. 
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f: #typographic apostrophes in the data, ensure_ascii=False keeps them as it is so they write correctly
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    """Parses NIST data file and writes structured records to JSONL file"""
    records = parse_nist("corpus/raw/nist_core.html")
    write_jsonl(records, OUTPUT_PATH)
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")

