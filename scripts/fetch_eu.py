"""Downalods the EU AI Act article pages from artificialintelligenceact.eu and record their checksums. Kept as a seperate script from fetch_nist as this involves a heavier and complex pipeline."""

import hashlib
import time
from pathlib import Path

import requests

ARTICLE_URL_BASE = "https://artificialintelligenceact.eu/article/{n}/"
ARTICLE_COUNT = 113

RAW_DIR = Path("corpus/raw")
EU_DIR = RAW_DIR / "eu_articles"

HEADERS = { #To bypass anti-bot protocols by making the request claim to be a real Chrome browser
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def fetch_one(filename: str, url: str, directory: Path) -> tuple[str, int]:
    """The resuable core, downloads the content for each article and saved them to directory/filename, returns (sha256 checksum, byte_count)"""
    response = requests.get(url, timeout = 30, headers = HEADERS)
    response.raise_for_status() #error handling

    path = directory / filename
    path.write_bytes(response.content) #writes the actual content

    digest = hashlib.sha256(response.content).hexdigest() #conputes checksum per article
    return digest, len(response.content) #byte_count for sanity check

def fetch_articles() -> None:
    """Main orchestration of the downloading of all 113 Articles and computing checksums for each one"""
    EU_DIR.mkdir(parents = True, exist_ok = True)
    checksums = []

    for n in range(1, ARTICLE_COUNT + 1):
        filename = f"article_{n}.html"
        url = ARTICLE_URL_BASE.format(n = n)

        try: #error handling, use try/except
            digest, size = fetch_one(filename, url, EU_DIR)
            checksums.append(f"{filename} {size:>7} bytes sha256 = {digest}")
            print(f"[{n:>3}/{ARTICLE_COUNT}] {filename} {size} bytes")
        except requests.RequestException as e:
            print(f"[{n:>3}/{ARTICLE_COUNT}] FAILED: {url} ({e})")
            checksums.append(f"{filename} FAILED {e}") #record down which files failed for debugging, dont crash the whole script on one failure

        time.sleep(0.5) #protect against rate limits

    checksum_path = RAW_DIR / "eu_checksums.txt"
    checksum_path.write_text("\n".join(checksums) + "\n", encoding = "utf-8")
    print(f"\nWrote checksums for {len(checksums)} articles to {checksum_path}")

if __name__ == "__main__":
    print(f"Fetching {ARTICLE_COUNT} EU AI ACT article pages (Will take around 1 minute)")
    fetch_articles()



