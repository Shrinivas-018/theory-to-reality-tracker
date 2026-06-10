"""Inspect and fix lineage graph by recategorizing ideas and regenerating edges."""
import json
import os
from collections import defaultdict
from datetime import datetime

DATA_DIR = os.path.join("data", "evolution_tracker_api")
ideas_path = os.path.join(DATA_DIR, "ideas.json")
edges_path = os.path.join(DATA_DIR, "edges.json")

# ─── STEP 1: Load ideas ────────────────────────────────────────
with open(ideas_path, "r", encoding="utf-8") as f:
    ideas_dict = json.load(f)

print(f"Total ideas: {len(ideas_dict)}")

# Count categories
cats = defaultdict(int)
for v in ideas_dict.values():
    cats[v["category"]] += 1
print("\nCurrent categories:")
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")

# ─── STEP 2: Auto-categorize "General Science" ─────────────────
CATEGORY_MAP = {
    # Physics
    "optics": "Physics", "quantum": "Physics", "thermodynamics": "Physics",
    "mechanics": "Physics", "electromagnetism": "Physics", "nuclear": "Physics",
    "photon": "Physics", "particle": "Physics", "acoustics": "Physics",
    "laser": "Physics", "spectroscopy": "Physics", "plasma": "Physics",
    "relativity": "Physics", "astrophysics": "Physics", "cosmology": "Physics",
    "gravitational": "Physics", "magnetic": "Physics", "radiation": "Physics",
    "semiconductor": "Physics", "superconductor": "Physics",
    
    # Biology / Life Sciences
    "biology": "Biology", "genetics": "Biology", "molecular": "Biology",
    "cell": "Biology", "microbiology": "Biology", "ecology": "Biology",
    "zoology": "Biology", "botany": "Biology", "evolution": "Biology",
    "neuroscience": "Biology", "anatomy": "Biology", "physiology": "Biology",
    "genomics": "Biology", "proteomics": "Biology", "bioinformatics": "Biology",
    "taxon": "Biology", "organism": "Biology", "virology": "Biology",
    "immunology": "Biology", "pathology": "Biology", "biochemistry": "Biology",
    "biophysics": "Biology", "computational biology": "Biology",
    
    # Medicine / Health
    "medicine": "Medicine", "clinical": "Medicine", "surgery": "Medicine",
    "cardiology": "Medicine", "oncology": "Medicine", "pharmacology": "Medicine",
    "epidemiology": "Medicine", "pathogen": "Medicine", "vaccine": "Medicine",
    "radiology": "Medicine", "anesthesia": "Medicine", "psychiatry": "Medicine",
    "dermatology": "Medicine", "pediatrics": "Medicine", "nursing": "Medicine",
    "toxicology": "Medicine", "biomedical": "Medicine",
    
    # Chemistry
    "chemistry": "Chemistry", "chemical": "Chemistry", "polymer": "Chemistry",
    "catalysis": "Chemistry", "crystallography": "Chemistry",
    "electrochemistry": "Chemistry", "organic": "Chemistry",
    "inorganic": "Chemistry", "analytical": "Chemistry",
    
    # Computer Science / Tech
    "computer": "Computer Science", "algorithm": "Computer Science",
    "machine learning": "Computer Science", "artificial intelligence": "Computer Science",
    "programming": "Computer Science", "database": "Computer Science",
    "software": "Computer Science", "network": "Computer Science",
    "cryptography": "Computer Science", "data mining": "Computer Science",
    "natural language processing": "Computer Science", "robotics": "Computer Science",
    "simulation": "Computer Science", "operating system": "Computer Science",
    "parallel computing": "Computer Science", "computer vision": "Computer Science",
    
    # Mathematics
    "mathematics": "Mathematics", "algebra": "Mathematics", "geometry": "Mathematics",
    "calculus": "Mathematics", "statistics": "Mathematics", "probability": "Mathematics",
    "combinatorics": "Mathematics", "topology": "Mathematics",
    "number theory": "Mathematics", "mathematical": "Mathematics",
    
    # Engineering
    "engineering": "Engineering", "mechanical": "Engineering", "electrical": "Engineering",
    "civil": "Engineering", "aerospace": "Engineering", "materials": "Engineering",
    "manufacturing": "Engineering", "control theory": "Engineering",
    "signal processing": "Engineering", "telecommunications": "Engineering",
    "embedded": "Engineering", "microelectronics": "Engineering",
    
    # Earth / Environmental
    "geology": "Earth Sciences", "oceanography": "Earth Sciences",
    "meteorology": "Earth Sciences", "seismology": "Earth Sciences",
    "climate": "Environmental Science", "environmental": "Environmental Science",
    "hydrology": "Earth Sciences", "geophysics": "Earth Sciences",
    "paleontology": "Earth Sciences", "mineralogy": "Earth Sciences",
    
    # Social Sciences
    "psychology": "Psychology", "cognitive": "Psychology", "behavioral": "Psychology",
    "sociology": "Sociology", "social": "Sociology", "anthropology": "Sociology",
    "economics": "Economics", "econometrics": "Economics", "finance": "Economics",
    "political": "Political Science", "law": "Political Science",
    "linguistics": "Linguistics", "philosophy": "Philosophy",
    "education": "Education", "pedagogy": "Education",
    "history": "History", "archaeology": "History",
    "geography": "Geography",
    
    # Arts
    "art": "Art", "music": "Art", "literature": "Art", "aesthetics": "Art",
}

recategorized = 0
for idea_id, idea in ideas_dict.items():
    if idea["category"] != "General Science":
        continue
    
    # Check title and keywords against category map
    title_lower = idea.get("title", "").lower()
    desc_lower = idea.get("description", "").lower()
    keywords = idea.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [keywords]
    kw_text = " ".join(k.lower() for k in keywords)
    
    search_text = f"{title_lower} {desc_lower} {kw_text}"
    
    new_cat = None
    for keyword, category in CATEGORY_MAP.items():
        if keyword in search_text:
            new_cat = category
            break
    
    if new_cat:
        idea["category"] = new_cat
        recategorized += 1

print(f"\nRecategorized: {recategorized} ideas")

# Count new categories
cats2 = defaultdict(int)
for v in ideas_dict.values():
    cats2[v["category"]] += 1
print("\nNew categories:")
for c, n in sorted(cats2.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")

# Save updated ideas
with open(ideas_path, "w", encoding="utf-8") as f:
    json.dump(ideas_dict, f, indent=2)
print(f"\nSaved updated ideas to {ideas_path}")

# ─── STEP 3: Regenerate edges with better strategies ──────────
ideas = list(ideas_dict.values())
ideas.sort(key=lambda x: x["start_year"])

edges = []
seen = set()

# Strategy 1: Same category, temporal chain (skip if only 1 idea in category)
by_category = defaultdict(list)
for idea in ideas:
    by_category[idea["category"]].append(idea)

for cat, cat_ideas in by_category.items():
    if len(cat_ideas) < 2:
        continue
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

# Strategy 2: Cross-category keyword overlap
kw_index = defaultdict(list)
for idea in ideas:
    kws = idea.get("keywords", [])
    if isinstance(kws, str):
        kws = [kws]
    for kw in kws:
        kw_lower = kw.lower().strip()
        if len(kw_lower) > 2:
            kw_index[kw_lower].append(idea)

for kw, kw_ideas in kw_index.items():
    if len(kw_ideas) < 2 or len(kw_ideas) > 15:
        continue
    kw_ideas_sorted = sorted(kw_ideas, key=lambda x: x["start_year"])
    for i in range(len(kw_ideas_sorted)):
        for j in range(i + 1, min(i + 3, len(kw_ideas_sorted))):
            src = kw_ideas_sorted[i]
            tgt = kw_ideas_sorted[j]
            if src["id"] == tgt["id"] or src["category"] == tgt["category"]:
                continue
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

# Strategy 3: Stage progression (philosophy -> validation -> engineering -> modern)
stage_order = ["philosophy", "scientific_validation", "engineering_application", "modern_technology"]
by_stage = defaultdict(list)
for idea in ideas:
    by_stage[idea["stage"]].append(idea)

for si in range(len(stage_order) - 1):
    curr_stage = stage_order[si]
    next_stage = stage_order[si + 1]
    for ci in by_stage.get(curr_stage, []):
        ci_kws = set(k.lower() for k in (ci.get("keywords", []) if isinstance(ci.get("keywords", []), list) else [ci.get("keywords", "")]))
        ci_cat = ci["category"]
        
        best_match = None
        best_score = 0
        
        for ni in by_stage.get(next_stage, []):
            ni_kws = set(k.lower() for k in (ni.get("keywords", []) if isinstance(ni.get("keywords", []), list) else [ni.get("keywords", "")]))
            
            score = 0
            # Same category = strong match
            if ci_cat == ni["category"]:
                score += 3
            # Keyword overlap
            overlap = len(ci_kws & ni_kws)
            score += overlap * 2
            # Title similarity (partial)
            if ci["title"].lower().split()[0] == ni["title"].lower().split()[0]:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = ni
        
        if best_match and best_score > 0:
            key = (ci["id"], best_match["id"])
            if key not in seen and ci["id"] != best_match["id"]:
                seen.add(key)
                edges.append({
                    "source_id": ci["id"],
                    "target_id": best_match["id"],
                    "influence_type": "applied_to",
                    "influence_weight": round(0.7 + 0.1 * best_score, 4),
                    "evidence": f"Stage progression: {curr_stage} -> {next_stage}",
                    "confidence_score": 0.75,
                })

# Strategy 4: Connect parent disciplines to sub-disciplines
DISCIPLINE_HIERARCHY = {
    "Physics": ["Engineering", "Materials Science", "Earth Sciences"],
    "Biology": ["Medicine", "Environmental Science"],
    "Chemistry": ["Medicine", "Materials Science", "Engineering"],
    "Mathematics": ["Computer Science", "Physics", "Economics"],
    "Computer Science": ["Engineering"],
    "Philosophy": ["Psychology", "Sociology", "Political Science", "Education"],
    "Psychology": ["Education", "Sociology"],
}

for parent_cat, child_cats in DISCIPLINE_HIERARCHY.items():
    parent_ideas = [i for i in ideas if i["category"] == parent_cat]
    for child_cat in child_cats:
        child_ideas = [i for i in ideas if i["category"] == child_cat]
        if not parent_ideas or not child_ideas:
            continue
        # Connect earliest parent to earliest child
        parent_ideas.sort(key=lambda x: x["start_year"])
        child_ideas.sort(key=lambda x: x["start_year"])
        src = parent_ideas[0]
        tgt = child_ideas[0]
        key = (src["id"], tgt["id"])
        if key not in seen and src["id"] != tgt["id"]:
            seen.add(key)
            edges.append({
                "source_id": src["id"],
                "target_id": tgt["id"],
                "influence_type": "foundational",
                "influence_weight": 0.9,
                "evidence": f"Discipline hierarchy: {parent_cat} -> {child_cat}",
                "confidence_score": 0.9,
            })

# Add timestamps
now = datetime.now().isoformat()
for edge in edges:
    edge["created_at"] = now

# Save edges
with open(edges_path, "w", encoding="utf-8") as f:
    json.dump(edges, f, indent=2)

s1 = sum(1 for e in edges if e["influence_type"] == "derived_from")
s2 = sum(1 for e in edges if e["influence_type"] == "inspired_by")
s3 = sum(1 for e in edges if e["influence_type"] == "applied_to")
s4 = sum(1 for e in edges if e["influence_type"] == "foundational")
print(f"\nGenerated {len(edges)} edges:")
print(f"  Category chains (derived_from): {s1}")
print(f"  Keyword overlap (inspired_by):  {s2}")
print(f"  Stage progression (applied_to): {s3}")
print(f"  Discipline hierarchy (foundational): {s4}")

# ─── STEP 4: Push updated data to MongoDB ─────────────────────
print("\n--- Syncing to MongoDB ---")
try:
    from dotenv import load_dotenv
    load_dotenv()
    from pymongo import MongoClient
    import time
    
    uri = os.getenv("MONGODB_ATLAS_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGODB_DATABASE", "yuga_evolution_db")
    is_atlas = "mongodb+srv://" in uri
    
    params = {
        "serverSelectionTimeoutMS": 30000,
        "connectTimeoutMS": 30000,
        "retryWrites": True,
    }
    if is_atlas:
        params["ssl"] = True
        params["tlsInsecure"] = True
    
    client = MongoClient(uri, **params)
    client.server_info()
    db = client[db_name]
    
    # Update ideas
    ideas_coll = db["evolution_ideas"]
    updated = 0
    for idea_id, idea in ideas_dict.items():
        idea["id"] = idea_id
        ideas_coll.replace_one({"id": idea_id}, idea, upsert=True)
        updated += 1
    print(f"  Updated {updated} ideas in MongoDB")
    
    # Replace edges
    edges_coll = db["evolution_edges"]
    edges_coll.delete_many({})
    if edges:
        edges_coll.insert_many(edges, ordered=False)
    print(f"  Inserted {len(edges)} edges in MongoDB")
    
    client.close()
    print("  MongoDB sync complete!")
except Exception as e:
    print(f"  MongoDB sync failed: {e}")
    print("  JSON files are updated — restart server to reload")

print("\nDone! Restart the backend to see the updated lineage graph.")
