"""Downloads the source documents once from the internet and record their checksums"""
from fileinput import filename
from pathlib import Path

import hashlib
from urllib import response
import requests

SOURCES = {
    "nist_core.html": "https://airc.nist.gov/airmf-resources/airmf/5-sec-core/"
}

RAW_DIR = Path("corpus/raw")

def fetch(filename:str, url:str):
    """Downloads url, saves to corpus/raw/filename, and returns its SHA-256 digital fingerprint for checksum verification"""    
    response = requests.get(url, timeout = 20)
    response.raise_for_status() #raises exception on a bad status code. Without it, the script will continue to save an error page. 

    path = RAW_DIR / filename
    path.write_bytes(response.content)

    digest = hashlib.sha256(response.content).hexdigest() #Uses SHA256 hashing to generate a checksum for the downloaded file. This is useful for verifying the integrity of the file (whether the file is identitcal to the one I used to run the tests on for this project) later on.
    print(f"{filename} {len(response.content):>8} bytes sha256 = {digest}")
    return digest

if __name__ == "__main__":
    RAW_DIR.mkdir(parents = True, exist_ok = True)
    for filename, url in SOURCES.items():
        fetch(filename, url)