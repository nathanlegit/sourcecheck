"""Parse the AU AI Article HTML into structured records similar to that of NIST, chunked by numebred clause"""

import json
import re #need to use regex 
from pathlib import Path

from lxml import html

RAW_DIR = Path("corpus/raw/eu_articles")
OUTPUT_PATH = Path("corpus/parsed/eu_ai_act.jsonl") #similar to parse_nist, use jsonl file for streaming, git tracking etc
ARTICLE_COUNT = 113
SOURCE_URL_TEMPLATE = "https://artificialintelligenceact.eu/article/{n}/"
RETRIEVED = "2026-08-22"

CONTENT_DIV_XPATH = "//div[contains(@class, 'et_pb_post_content')]"
TITLE_XPATH = "//h1[@class = 'entry-title']"

CLAUSE_START = re.compile(r"^\d+\.\s") #regex expression that matches the number in front of a numbered clause "i.e. 1. ... or 3. ..."

def normalise(text: str) -> str:
    """Normalises EU AI text by collapsing whitespace (not only stripping) to single spaces and trimming leading/trailing whitespace"""
    return " ".join(text.split())


def canonical_id(article_num: int, clause_num: int) -> str:
    """ Standardises the chunk id format to follow NIST format"""
    return f"eu:article-{article_num}-{clause_num}"

def parse_article(html_path: Path, article_num: int) -> list[dict]:
    """Parses one article and returns a list of dictionaries in the structured format that follows the NIST data"""
    doc = html.parse(str(html_path)).getroot()

    #Gets the Article Title out
    title_raw = doc.xpath(TITLE_XPATH)
    if title_raw:
        title = normalise(title_raw[0].text_content())
    else:
        title = f"Article {article_num}"

    content_divs = doc.xpath(CONTENT_DIV_XPATH)
    if not content_divs:
        raise ValueError(f"No content div found for article {article_num}")
    content_div = content_divs[0] #gets out the part of the html with the legal content that we need

    paragraphs = content_div.xpath(".//p") #since every single clause is wrapped in <p> tags

    clean_paragraphs = []
    for p in paragraphs:
        text = normalise(p.text_content())
        if not text or text.startswith("Related:"): #From inspection, we noticed a few paragraphs in the content were Related Articles: xx, which we wanted to exclude from the data
            continue
        clean_paragraphs.append(text)

    records = []
    clause_num = 0
    current_text_parts = []

    def flush():
        """After every numbered clause if finished processing, flush adds this numbered clause (together with any sub points if applicable) to records"""
        if clause_num > 0 and current_text_parts:
            records.append({
                "chunk_id": canonical_id(article_num, clause_num),
                "display_id": f"Article {article_num}({clause_num})",
                "document": "EU AI Act 2024/1689",
                "article_num": article_num,
                "article_title": title,
                "text": " ".join(current_text_parts),
                "scored": True,
                "source_url": SOURCE_URL_TEMPLATE.format(n = article_num),
                "retrieved": RETRIEVED,
            })
                
            
        
    for text in clean_paragraphs:
        if CLAUSE_START.match(text):
            flush()
            clause_num += 1
            current_text_parts = [text]
        else: #for the subpoints that do not start with a number
            if clause_num == 0:
                continue
            current_text_parts.append(text)

    flush()

    # Fallback: no numbered clauses found at all, treat whole article as one chunk
    if not records and clean_paragraphs:
        records.append({
            "chunk_id": canonical_id(article_num, 1),
            "display_id": f"Article {article_num}",
            "document": "EU AI Act 2024/1689",
            "article_num": article_num,
            "article_title": title,
            "text": " ".join(clean_paragraphs),
            "scored": True,
            "source_url": SOURCE_URL_TEMPLATE.format(n=article_num),
            "retrieved": RETRIEVED,
        })


    return records

    """quite interesting design of the parser, but we design it this way because we need to allow 
    for the sub points (that start with a letter but is also wrapped in a <p> tag) to be appended to each numbered clause.
    hence we define a flush() in this function"""

def parse_all() -> list[dict]:
    """parses all 113 articles in the AU AI Act"""
    all_records = []
    for n in range(1, ARTICLE_COUNT + 1):
        path = RAW_DIR / f"article_{n}.html"
        records = parse_article(path, n)
        all_records.extend(records) # use extend instead of append to flatten the list, so its not a list of lists
    return all_records

def write_jsonl(records: list[dict], path: Path) -> None:
    """write structured records into a jsonl file for embedding"""
    path.parent.mkdir(parents = True, exist_ok = True)
    with path.open("w", encoding = "utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii = False) + "\n")

if __name__ == "__main__":
    records = parse_all()
    write_jsonl(records, OUTPUT_PATH)
    print(f"Parsed {len(records)} claused from {ARTICLE_COUNT} articles")
    for r in records[:3]: #sanity check
        print(r)
            
