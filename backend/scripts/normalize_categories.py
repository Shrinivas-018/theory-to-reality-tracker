"""Normalize duplicate category names (case differences)."""
import json
import os

# Map lowercased duplicates to canonical forms
NORMALIZE = {
    "computer science": "Computer Science",
    "political science": "Political Science",
    "materials science": "Materials Science",
    "environmental science": "Environmental Science",
}

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "data", "evolution_tracker_api", "ideas.json")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for idea_id, idea in data.items():
        cat_lower = idea["category"].lower()
        if cat_lower in NORMALIZE and idea["category"] != NORMALIZE[cat_lower]:
            old = idea["category"]
            idea["category"] = NORMALIZE[cat_lower]
            changed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Count
    cat_counts = {}
    for idea in data.values():
        cat_counts[idea["category"]] = cat_counts.get(idea["category"], 0) + 1

    print(f"Normalized {changed} category names")
    print(f"\nFinal Distribution ({len(cat_counts)} categories):")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()
