"""Check remaining General Science ideas and do a second pass."""
import json

path = "data/evolution_tracker_api/ideas.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

gs = [(k, v) for k, v in data.items() if v["category"] == "General Science"]
print(f"Remaining General Science: {len(gs)}")
print()
for kid, idea in gs[:40]:
    print(f"  {idea['title'][:50]:50s} | kw: {idea['keywords'][:3]}")
