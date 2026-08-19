"""Inspects the NIST dataset before we build the parer. Throwaway code, will not be committed."""

from pathlib import Path

from lxml import html

doc = html.parse("corpus/raw/nist_core.html").getroot()

tables = doc.xpath("//table")
print(f"Found {len(tables)} tables\n")

for i, table in enumerate(tables):
    rows = table.xpath(".//tr")
    print(f"=== Table {i}: {len(rows)} rows")

    for row in rows[:4]:
        cells = row.xpath("./td | ./th")
        print(f"  row: {len(cells)} cells")
        for cell in cells:
            text = " ".join(cell.text_content().split())
            print(f"    tag={cell.tag} rowspan={cell.get('rowspan')!r} :: {text[:80]}")
    print()