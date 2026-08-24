"""Inspects the EU AI Act HTML pages before we build the parer. Throwaway code, will not be committed. Was used as a preliminary inspection, see inspect_eu_micro for the second step of inspection"""

from pathlib import Path
from lxml import html

doc = html.parse("corpus/raw/eu_articles/article_1.html") #use Article 1 as sample

articles = doc.xpath("//article") #Find candidate content containers, articles on WordPress sites are usually wrapped in <article>, or a <div> with a content-ish class/id
print(f"Found {len(articles)} <article> elements\n")

for i, art in enumerate(articles):
    print(f"--- <article> {i}: id = {art.get('id')!r} class = {art.get('class')!r}") #!r called repr(), which shows you Python's own representation of a value (quotes around string, None printed literally) rather than str() more casual conversion
    text_preview = " ".join(art.text_content().split())[:200]
    print(f".   preview:{text_preview}\n")

headings = doc.xpath("//h1 | //h2 | //h3 | //h4") #Look for headings that might mark the title, Summary box, and body
print(f"\nFound {len(headings)} headings\n")
for h in headings:
    text = " ".join(h.text_content().split())
    print(f" <{h.tag}> class = {h.get('class')!r}: {text[:80]}")

"""Note on findings from this prelimary inspection: The html page does not use any <article> tag, and the five headings map almost exactly to teh page actual sections

<h2>          Table of contents          ← the giant nav list of all 113 articles
<h1 class="entry-title">   Article 1: Subject Matter   ← title
<h4>          Summary                    ← the CLaiRK box, to be excluded

** Where the actual numbered legal text is at **

<h4>          Suitable Recitals          ← footer cross-references, not needed
<h2 class="...">   Receive EU AI Act updates...   ← newsletter signup, to be ignored


However, we still do not know what element wraps the numbered legal paragraphs and how it looks (1. ... / (1) ... / (a) ...)
Refer to inspect_eu_micro.py for the further inspection
 """