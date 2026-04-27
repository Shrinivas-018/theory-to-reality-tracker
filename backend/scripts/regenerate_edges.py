"""
Regenerate influence edges for the lineage graph.

Reads existing ideas from the DataStore and creates meaningful edges
based on category hierarchy, stage progression, and keyword similarity.
This fixes the issue where the OpenAlex list API doesn't return
ancestor/related_concepts, resulting in 0 edges.
"""

import json
import re
from collections import defaultdict
from backend.models import InfluenceEdge, EvolutionStage
from backend.services import DataStore

# Stage ordering for hierarchy connections
STAGE_ORDER = {
    "philosophy": 0,
    "scientific_validation": 1,
    "engineering_application": 2,
    "modern_technology": 3,
}

# Known parent-child discipline relationships
DISCIPLINE_HIERARCHY = {
    "Quantum mechanics": "Physics",
    "Optics": "Physics",
    "Atomic physics": "Physics",
    "Thermodynamics": "Physics",
    "Mechanics": "Physics",
    "Electromagnetism": "Physics",
    "Organic chemistry": "Chemistry",
    "Biochemistry": "Chemistry",
    "Analytical chemistry": "Chemistry",
    "Inorganic chemistry": "Chemistry",
    "Genetics": "Biology",
    "Microbiology": "Biology",
    "Ecology": "Biology",
    "Botany": "Biology",
    "Zoology": "Biology",
    "Virology": "Biology",
    "Molecular biology": "Biology",
    "Computational biology": "Biology",
    "Neuroscience": "Biology",
    "Artificial intelligence": "Computer science",
    "Machine learning": "Computer science",
    "Database": "Computer science",
    "Algorithm": "Computer science",
    "Data mining": "Computer science",
    "Computer vision": "Computer science",
    "Computer network": "Computer science",
    "Telecommunications": "Engineering",
    "Chemical engineering": "Engineering",
    "Electrical engineering": "Engineering",
    "Internal medicine": "Medicine",
    "Surgery": "Medicine",
    "Pathology": "Medicine",
    "Radiology": "Medicine",
    "Cardiology": "Medicine",
    "Endocrinology": "Medicine",
    "Pharmacology": "Medicine",
    "Nursing": "Medicine",
    "Medical education": "Medicine",
    "Immunology": "Medicine",
    "Calculus": "Mathematics",
    "Statistics": "Mathematics",
    "Combinatorics": "Mathematics",
    "Pure mathematics": "Mathematics",
    "Geometry": "Mathematics",
    "Algebra": "Mathematics",
    "Crystallography": "Chemistry",
    "Metallurgy": "Materials science",
    "Oceanography": "Geography",
    "Astronomy": "Physics",
    "Paleontology": "Geology",
    "Horticulture": "Biology",
    "Public relations": "Business",
    "Management": "Business",
    "Marketing": "Business",
    "Accounting": "Business",
    "Finance": "Economics",
    "Microeconomics": "Economics",
    "Macroeconomics": "Economics",
    "Sociology": "Political science",
    "Law": "Political science",
    "Literature": "Art",
    "Art history": "Art",
    "Epistemology": "Philosophy",
    "Laser": "Physics",
    "Catalysis": "Chemistry",
    "Magnetic field": "Physics",
    "Doppler effect": "Physics",
    "Remote sensing": "Engineering",
}

# Cross-discipline influence links (source → target)
CROSS_DISCIPLINE = [
    ("Physics", "Chemistry"),
    ("Physics", "Engineering"),
    ("Chemistry", "Biology"),
    ("Chemistry", "Materials science"),
    ("Biology", "Medicine"),
    ("Mathematics", "Physics"),
    ("Mathematics", "Computer science"),
    ("Computer science", "Engineering"),
    ("Philosophy", "Psychology"),
    ("Psychology", "Sociology"),
    ("Economics", "Political science"),
    ("Physics", "Astronomy"),
    ("Geology", "Environmental science"),
    ("Biology", "Environmental science"),
]

import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data", "evolution_tracker_api")
    store = DataStore(data_dir=data_dir)
    ideas = store.get_all_ideas()

    if not ideas:
        print("No ideas found. Run fetch_openalex first.")
        return

    # Build lookup maps
    id_to_idea = {idea.id: idea for idea in ideas}
    title_to_id = {idea.title: idea.id for idea in ideas}
    category_to_ids = defaultdict(list)
    for idea in ideas:
        category_to_ids[idea.category].append(idea.id)

    edges = []
    seen = set()

    def add_edge(src_id, tgt_id, inf_type, weight, evidence, confidence):
        key = (src_id, tgt_id)
        if key in seen or src_id == tgt_id:
            return
        if src_id not in id_to_idea or tgt_id not in id_to_idea:
            return
        seen.add(key)
        edges.append(InfluenceEdge(
            source_id=src_id,
            target_id=tgt_id,
            influence_type=inf_type,
            influence_weight=weight,
            evidence=evidence,
            confidence_score=confidence,
        ))

    # === 1. Discipline hierarchy edges (sub-discipline → parent) ===
    for child_name, parent_name in DISCIPLINE_HIERARCHY.items():
        child_id = title_to_id.get(child_name)
        parent_id = title_to_id.get(parent_name)
        if child_id and parent_id:
            add_edge(parent_id, child_id, "derived_from", 0.85,
                     "Discipline hierarchy", 0.95)

    # === 2. Within-category stage progression ===
    # Connect ideas in the same category from earlier to later stages
    for category, ids in category_to_ids.items():
        if len(ids) < 2:
            continue
        # Sort by stage order then by start_year
        sorted_ids = sorted(ids, key=lambda i: (
            STAGE_ORDER.get(id_to_idea[i].stage.value
                            if hasattr(id_to_idea[i].stage, 'value')
                            else id_to_idea[i].stage, 99),
            id_to_idea[i].start_year
        ))
        # Connect consecutive ideas in the chain
        for i in range(len(sorted_ids) - 1):
            src = sorted_ids[i]
            tgt = sorted_ids[i + 1]
            add_edge(src, tgt, "derived_from", 0.7,
                     f"Stage progression within {category}", 0.8)

    # === 3. Cross-discipline edges ===
    for src_name, tgt_name in CROSS_DISCIPLINE:
        src_id = title_to_id.get(src_name)
        tgt_id = title_to_id.get(tgt_name)
        if src_id and tgt_id:
            add_edge(src_id, tgt_id, "inspired_by", 0.5,
                     "Cross-discipline influence", 0.7)

    # === 4. Connect "General Science" orphans to their likely parent ===
    # Use title keywords to infer parent discipline
    for idea in ideas:
        if idea.category != "General Science":
            continue
        title_lower = idea.title.lower()
        # Check if title or keywords match a known discipline hierarchy
        for child_name, parent_name in DISCIPLINE_HIERARCHY.items():
            if child_name.lower() in title_lower:
                parent_id = title_to_id.get(parent_name)
                if parent_id:
                    add_edge(parent_id, idea.id, "derived_from", 0.6,
                             f"Keyword match to {parent_name}", 0.7)
                break
        else:
            # Try matching against top-level discipline names
            for disc in ["Physics", "Chemistry", "Biology", "Mathematics",
                         "Computer science", "Medicine", "Engineering",
                         "Psychology", "Economics", "Philosophy"]:
                if disc.lower() in title_lower or any(
                    disc.lower() in kw.lower() for kw in idea.keywords
                ):
                    disc_id = title_to_id.get(disc)
                    if disc_id:
                        add_edge(disc_id, idea.id, "derived_from", 0.5,
                                 f"Keyword match to {disc}", 0.6)
                    break

    # === 5. Connect ideas that share laureates (collaborative link) ===
    laureate_to_ids = defaultdict(set)
    for idea in ideas:
        for laureate in idea.laureates:
            if laureate not in ("Unknown Scholar",):
                laureate_to_ids[laureate].add(idea.id)

    for laureate, idea_ids in laureate_to_ids.items():
        if len(idea_ids) < 2:
            continue
        id_list = sorted(idea_ids, key=lambda i: id_to_idea[i].start_year)
        # Connect the first two to avoid too many edges
        for i in range(min(len(id_list) - 1, 2)):
            add_edge(id_list[i], id_list[i + 1], "inspired_by", 0.4,
                     f"Shared contributor: {laureate}", 0.5)

    # Save edges to data store
    # Clear existing edges first
    edges_file = store.edges_file
    with open(edges_file, 'w', encoding='utf-8') as f:
        json.dump([e.to_dict() for e in edges], f, indent=2)

    print(f"[OK] Generated {len(edges)} influence edges")
    print(f"   Categories with edges: {len(category_to_ids)}")
    print(f"   Discipline hierarchy edges: {sum(1 for e in edges if e.evidence == 'Discipline hierarchy')}")
    print(f"   Stage progression edges: {sum(1 for e in edges if 'Stage progression' in e.evidence)}")
    print(f"   Cross-discipline edges: {sum(1 for e in edges if 'Cross-discipline' in e.evidence)}")
    print(f"   Keyword match edges: {sum(1 for e in edges if 'Keyword match' in e.evidence)}")
    print(f"   Shared contributor edges: {sum(1 for e in edges if 'Shared contributor' in e.evidence)}")
    print(f"\n[INFO] Restart the API to load the new edges: python -m backend.api")


if __name__ == "__main__":
    main()
