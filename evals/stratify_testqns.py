"""Stratified random sampling that picks out articles for us to build the 18 normal test questions on"""

import json
import random
from collections import defaultdict

random.seed(42)  # reproducible sample

def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f]

nist = load("corpus/parsed/nist.jsonl")
eu = load("corpus/parsed/eu_ai_act.jsonl")

# Stratify NIST by function, sample evenly
by_function = defaultdict(list)
for r in nist:
    by_function[r["function"]].append(r)

print("=== NIST sample (2 per function) ===\n")
for function, records in by_function.items():
    for r in random.sample(records, min(2, len(records))):
        print(f"{r['display_id']}: {r['text']}\n")

# Stratify EU by article ranges (spread across the document)
by_range = defaultdict(list)
for r in eu:
    bucket = r["article_num"] // 20  # groups of ~20 articles
    by_range[bucket].append(r)

print("\n=== EU AI Act sample (1-2 per article range) ===\n")
for bucket in sorted(by_range):
    for r in random.sample(by_range[bucket], min(2, len(by_range[bucket]))):
        print(f"{r['display_id']} ({r['article_title']}): {r['text']}\n")