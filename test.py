import json, random

with open("corpus/parsed/eu_ai_act.jsonl") as f:
    records = [json.loads(l) for l in f]

sample = random.sample(records, 8)
for r in sample:
    print(f"{r['display_id']}: {r['text'][:120]}")

for r in records:
    if r["article_num"] == 113:
        print(r)