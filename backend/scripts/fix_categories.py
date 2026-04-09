"""Fix duplicate categories and regenerate edges."""
import json

path = "data/evolution_tracker_api/ideas.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Merge duplicate categories
FIXES = {
    "Computer science": "Computer Science",
    "Physics": "Classical Physics",
    "Political science": "Political Science",
    "Materials science": "Materials Science",
    "Environmental science": "Environmental Science",
    "Psychology": "Neuroscience",
    "Sociology": "Philosophy",
    "Geology": "Earth Science",
    "Geography": "Earth Science",
    "Art": "Philosophy",
    "Business": "Economics",
    "History": "Philosophy",
}

changed = 0
for idea_id, idea in data.items():
    if idea["category"] in FIXES:
        idea["category"] = FIXES[idea["category"]]
        changed += 1

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

cat_counts = {}
for idea in data.values():
    cat_counts[idea["category"]] = cat_counts.get(idea["category"], 0) + 1

print(f"Fixed {changed} category names")
print(f"\nFinal: {len(cat_counts)} categories:")
for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

if __name__ == "__main__":
    pass
