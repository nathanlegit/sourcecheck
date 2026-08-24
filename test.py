import requests

url = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
response = requests.get(url, timeout=30, headers=headers)
print("status:", response.status_code)
print("content-type:", response.headers.get("content-type"))
print("bytes:", len(response.content))