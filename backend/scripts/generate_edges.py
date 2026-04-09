"""
Auto-generate influence edges between ideas based on keyword overlap
and temporal relationships. Creates meaningful connections for the
lineage graph visualization.
"""

import json
import os
from itertools import combinations
from collections import defaultdict


def generate_edges():
    """Generate edges from ideas based on keyword overlap and category relationships."""
    data_dir = os.path.join("data", "evolution_tracker_api")
    ideas_path = os.path.join(data_dir, "ideas.json")
    edges_path = os.path.join(data_dir, "edges.json")

    with open(ideas_path, "r", encoding="utf-8") as f:
        ideas_dict = json.load(f)

    ideas = list(ideas_dict.values())
    ideas.sort(key=lambda x: x["start_year"])

    edges = []
    seen = set()

    # --- Strategy 1: Same category, temporal chain ---
    # Within each category, connect ideas chronologically
    by_category = defaultdict(list)
    for idea in ideas:
        by_category[idea["category"]].append(idea)

    for cat, cat_ideas in by_category.items():
        cat_ideas.sort(key=lambda x: x["start_year"])
        for i in range(len(cat_ideas) - 1):
            src = cat_ideas[i]
            tgt = cat_ideas[i + 1]
            key = (src["id"], tgt["id"])
            if key not in seen:
                seen.add(key)
                edges.append({
                    "source_id": src["id"],
                    "target_id": tgt["id"],
                    "influence_type": "derived_from",
                    "influence_weight": round(0.6 + 0.3 * src.get("influence_score", 0.5), 4),
                    "evidence": f"Chronological evolution within {cat}",
                    "confidence_score": 0.8,
                })

    # --- Strategy 2: Keyword overlap across categories ---
    # Build a keyword-to-ideas index
    kw_index = defaultdict(list)
    for idea in ideas:
        for kw in idea.get("keywords", []):
            kw_lower = kw.lower().strip()
            if len(kw_lower) > 2:  # skip very short keywords
                kw_index[kw_lower].append(idea)

    for kw, kw_ideas in kw_index.items():
        if len(kw_ideas) < 2 or len(kw_ideas) > 20:
            continue  # skip too common or too rare keywords

        kw_ideas_sorted = sorted(kw_ideas, key=lambda x: x["start_year"])
        for i in range(len(kw_ideas_sorted)):
            for j in range(i + 1, min(i + 3, len(kw_ideas_sorted))):  # connect to next 2
                src = kw_ideas_sorted[i]
                tgt = kw_ideas_sorted[j]
                if src["id"] == tgt["id"]:
                    continue
                if src["category"] == tgt["category"]:
                    continue  # already handled by strategy 1

                key = (src["id"], tgt["id"])
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        "source_id": src["id"],
                        "target_id": tgt["id"],
                        "influence_type": "inspired_by",
                        "influence_weight": round(0.4 + 0.2 * src.get("influence_score", 0.5), 4),
                        "evidence": f"Shared keyword: '{kw}'",
                        "confidence_score": 0.6,
                    })

    # --- Strategy 3: Stage progression links ---
    # Connect philosophy → scientific_validation → engineering → technology
    stage_order = ["philosophy", "scientific_validation", "engineering_application", "modern_technology"]
    by_stage = defaultdict(list)
    for idea in ideas:
        by_stage[idea["stage"]].append(idea)

    for si in range(len(stage_order) - 1):
        curr_stage = stage_order[si]
        next_stage = stage_order[si + 1]
        curr_ideas = by_stage.get(curr_stage, [])
        next_ideas = by_stage.get(next_stage, [])

        for ci in curr_ideas:
            best_match = None
            best_overlap = 0
            ci_kws = set(k.lower() for k in ci.get("keywords", []))

            for ni in next_ideas:
                ni_kws = set(k.lower() for k in ni.get("keywords", []))
                overlap = len(ci_kws & ni_kws)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = ni

            if best_match and best_overlap > 0:
                key = (ci["id"], best_match["id"])
                if key not in seen and ci["id"] != best_match["id"]:
                    seen.add(key)
                    edges.append({
                        "source_id": ci["id"],
                        "target_id": best_match["id"],
                        "influence_type": "applied_to",
                        "influence_weight": round(0.7 + 0.2 * best_overlap / max(len(ci_kws), 1), 4),
                        "evidence": f"Stage progression: {curr_stage} → {next_stage}",
                        "confidence_score": 0.75,
                    })

    # Add created_at timestamp
    from datetime import datetime
    now = datetime.now().isoformat()
    for edge in edges:
        edge["created_at"] = now

    # Save
    with open(edges_path, "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2)

    print(f"✅ Generated {len(edges)} edges")
    print(f"   Strategy 1 (category chains): {sum(1 for e in edges if e['influence_type'] == 'derived_from')}")
    print(f"   Strategy 2 (keyword overlap): {sum(1 for e in edges if e['influence_type'] == 'inspired_by')}")
    print(f"   Strategy 3 (stage progression): {sum(1 for e in edges if e['influence_type'] == 'applied_to')}")
    print(f"   Saved to: {edges_path}")


if __name__ == "__main__":
    generate_edges()
