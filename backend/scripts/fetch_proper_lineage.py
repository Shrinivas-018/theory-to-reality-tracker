"""
Proper Lineage Data Fetcher

Uses OpenAlex real concept hierarchy:
  Level 0: Chemistry, Biology, Physics, Computer science...
  Level 1: Organic chemistry, Genetics, Quantum mechanics, AI...
  Level 2: Biochemistry, Molecular biology, Particle physics, ML...
  Level 3: Genomics, Bioinformatics, Deep learning...

Each concept's detail page has an `ancestors` list with parent IDs.
We use those to build REAL parent->child edges.
"""

import urllib.request
import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore

# ── LLM setup ────────────────────────────────────────────────────────────────
LLM_OK = False
llm = None
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
    KEY = os.getenv("GEMINI_API_KEY")
    if KEY:
        genai.configure(api_key=KEY)
        llm = genai.GenerativeModel("gemini-2.0-flash")
        LLM_OK = True
        print("[OK] Gemini 2.0 Flash ready")
    else:
        print("[WARN] No GEMINI_API_KEY")
except ImportError:
    print("[WARN] google-generativeai not installed")

# ── Stage mapping ─────────────────────────────────────────────────────────────
STAGE_MAP = {
    0: (EvolutionStage.PHILOSOPHY,            1800, 1850),
    1: (EvolutionStage.SCIENTIFIC_VALIDATION, 1850, 1950),
    2: (EvolutionStage.ENGINEERING_APPLICATION, 1950, 2000),
    3: (EvolutionStage.MODERN_TECHNOLOGY,     2000, 2025),
}

# ── Known authors ─────────────────────────────────────────────────────────────
AUTHORS: Dict[str, List[str]] = {
    "chemistry":               ["Antoine Lavoisier", "Marie Curie", "Linus Pauling"],
    "organic chemistry":       ["August Kekulé", "Emil Fischer", "Robert Burns Woodward"],
    "inorganic chemistry":     ["Alfred Werner", "Henry Taube", "F. Albert Cotton"],
    "physical chemistry":      ["Josiah Willard Gibbs", "Svante Arrhenius", "Peter Debye"],
    "analytical chemistry":    ["Robert Bunsen", "Gustav Kirchhoff", "Arnold Beckman"],
    "biochemistry":            ["Hans Krebs", "Frederick Sanger", "Paul Berg"],
    "polymer chemistry":       ["Hermann Staudinger", "Wallace Carothers", "Paul Flory"],
    "electrochemistry":        ["Michael Faraday", "Walther Nernst", "John Bockris"],
    "biology":                 ["Charles Darwin", "Gregor Mendel", "Carl Linnaeus"],
    "genetics":                ["Gregor Mendel", "Thomas Hunt Morgan", "Barbara McClintock"],
    "molecular biology":       ["James Watson", "Francis Crick", "Rosalind Franklin"],
    "cell biology":            ["Robert Hooke", "Matthias Schleiden", "Rudolf Virchow"],
    "ecology":                 ["Ernst Haeckel", "Charles Elton", "Eugene Odum"],
    "evolutionary biology":    ["Charles Darwin", "Ernst Mayr", "Stephen Jay Gould"],
    "microbiology":            ["Louis Pasteur", "Robert Koch", "Antonie van Leeuwenhoek"],
    "neuroscience":            ["Santiago Ramón y Cajal", "Charles Sherrington", "Eric Kandel"],
    "genomics":                ["Francis Collins", "Craig Venter", "Eric Lander"],
    "bioinformatics":          ["Margaret Dayhoff", "David Lipman", "Eugene Myers"],
    "physics":                 ["Isaac Newton", "Albert Einstein", "Richard Feynman"],
    "quantum mechanics":       ["Max Planck", "Niels Bohr", "Werner Heisenberg"],
    "thermodynamics":          ["Sadi Carnot", "Rudolf Clausius", "Ludwig Boltzmann"],
    "electromagnetism":        ["Michael Faraday", "James Clerk Maxwell", "Heinrich Hertz"],
    "optics":                  ["Ibn al-Haytham", "Isaac Newton", "Christiaan Huygens"],
    "nuclear physics":         ["Ernest Rutherford", "Enrico Fermi", "Lise Meitner"],
    "astrophysics":            ["Edwin Hubble", "Subrahmanyan Chandrasekhar", "Stephen Hawking"],
    "particle physics":        ["Paul Dirac", "Murray Gell-Mann", "Peter Higgs"],
    "condensed matter physics":["Lev Landau", "Philip Anderson", "John Bardeen"],
    "computer science":        ["Alan Turing", "John von Neumann", "Claude Shannon"],
    "artificial intelligence": ["Alan Turing", "John McCarthy", "Marvin Minsky"],
    "machine learning":        ["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
    "deep learning":           ["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
    "algorithms":              ["Donald Knuth", "Edsger Dijkstra", "Robert Tarjan"],
    "cryptography":            ["Claude Shannon", "Whitfield Diffie", "Ron Rivest"],
    "computer vision":         ["David Marr", "Yann LeCun", "Fei-Fei Li"],
    "natural language processing": ["Noam Chomsky", "Geoffrey Hinton", "Yoshua Bengio"],
    "programming language":    ["John Backus", "Dennis Ritchie", "Guido van Rossum"],
    "database":                ["Edgar F. Codd", "Michael Stonebraker", "Jim Gray"],
    "medicine":                ["Hippocrates", "Louis Pasteur", "Alexander Fleming"],
    "pharmacology":            ["Paul Ehrlich", "Gertrude Elion", "James Black"],
    "immunology":              ["Edward Jenner", "Louis Pasteur", "Paul Ehrlich"],
    "oncology":                ["Sidney Farber", "Judah Folkman", "Dennis Slamon"],
    "mathematics":             ["Euclid", "Carl Friedrich Gauss", "Henri Poincaré"],
    "calculus":                ["Isaac Newton", "Gottfried Leibniz", "Leonhard Euler"],
    "statistics":              ["Carl Friedrich Gauss", "Ronald Fisher", "Karl Pearson"],
    "algebra":                 ["Al-Khwarizmi", "Évariste Galois", "Emmy Noether"],
    "topology":                ["Henri Poincaré", "L.E.J. Brouwer", "John Milnor"],
    "engineering":             ["Archimedes", "Leonardo da Vinci", "Nikola Tesla"],
    "electrical engineering":  ["Michael Faraday", "Nikola Tesla", "Thomas Edison"],
    "mechanical engineering":  ["James Watt", "Rudolf Diesel", "George Stephenson"],
    "materials science":       ["William Henry Perkin", "Wallace Carothers", "Stephanie Kwolek"],
    "economics":               ["Adam Smith", "John Maynard Keynes", "Milton Friedman"],
    "psychology":              ["Sigmund Freud", "William James", "Ivan Pavlov"],
}

def get_authors(name: str) -> List[str]:
    nl = name.lower()
    for key, authors in AUTHORS.items():
        if key in nl or nl in key:
            return authors
    return ["Notable Researchers"]

# ── OpenAlex API ──────────────────────────────────────────────────────────────
def api_get(url: str) -> Optional[Dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "mailto:research@example.com"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"    [API ERR] {e}")
        return None

def fetch_level(level: int, per_page: int = 200) -> List[Dict]:
    data = api_get(f"https://api.openalex.org/concepts?filter=level:{level}&sort=works_count:desc&per-page={per_page}")
    return data.get("results", []) if data else []

def fetch_detail(concept_id: str) -> Optional[Dict]:
    return api_get(f"https://api.openalex.org/concepts/{concept_id}")

# ── LLM description enrichment ────────────────────────────────────────────────
def llm_describe(parent_name: str, children: List[Tuple[str, str]]) -> Dict[str, str]:
    """
    children: list of (name, existing_description)
    Returns: {name: enriched_description}
    """
    if not LLM_OK or not children:
        return {}

    items = "\n".join([f"- {name}: {desc[:120]}" for name, desc in children[:10]])
    prompt = f"""You are a science historian. "{parent_name}" has these sub-fields:

{items}

For each, write ONE clear sentence: what it is AND how it evolved from or specializes "{parent_name}".
Return ONLY a JSON object: {{"Sub-field name": "description"}}"""

    try:
        resp = llm.generate_content(prompt)
        text = resp.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"    [LLM ERR] {e}")
        return {}

# ── Main ──────────────────────────────────────────────────────────────────────
def build():
    ideas: Dict[str, IdeaNode] = {}   # id -> IdeaNode
    edges: List[InfluenceEdge] = []
    edge_set: set = set()

    def make_idea(cid, name, desc, level, category, works):
        stage, sy, ey = STAGE_MAP.get(min(level, 3), STAGE_MAP[3])
        max_w = 172_000_000  # approx max works_count in OpenAlex
        score = round(min(works / max_w, 1.0), 4)
        score = max(score, 0.05)
        return IdeaNode(
            id=cid, title=name[:100], description=(desc or f"A concept in {category}.")[:500],
            stage=stage, start_year=sy, end_year=ey,
            category=category, laureates=get_authors(name),
            motivation=f"{works:,} scholarly works",
            keywords=[name.lower()], influence_score=score,
        )

    def add_edge(src, tgt, itype, weight, evidence):
        key = (src, tgt)
        if key not in edge_set and src in ideas and tgt in ideas and src != tgt:
            edge_set.add(key)
            edges.append(InfluenceEdge(
                source_id=src, target_id=tgt,
                influence_type=itype, influence_weight=weight,
                evidence=evidence, confidence_score=0.9,
            ))

    # ── Level 0: Root fields ──────────────────────────────────────────────────
    print("\n[1/5] Fetching root fields (level 0)...")
    l0 = fetch_level(0, 50)
    for c in l0:
        cid = c["id"].split("/")[-1]
        name = c.get("display_name", "")
        ideas[cid] = make_idea(cid, name, c.get("description"), 0, name, c.get("works_count", 0))
    print(f"  {len(ideas)} root fields: {', '.join(i.title for i in list(ideas.values())[:8])}...")

    # ── Level 1: Sub-fields ───────────────────────────────────────────────────
    print("\n[2/5] Fetching sub-fields (level 1)...")
    l1 = fetch_level(1, 200)
    l1_added = 0
    parent_children: Dict[str, List[Tuple[str, str]]] = {}  # parent_id -> [(name, desc)]

    for c in l1[:80]:
        cid = c["id"].split("/")[-1]
        if cid in ideas:
            continue
        name = c.get("display_name", "")
        time.sleep(0.12)
        detail = fetch_detail(cid)
        if not detail:
            continue

        # Find level-0 parent from ancestors
        ancestors = detail.get("ancestors") or []
        parent_id = None
        category = None
        for anc in ancestors:
            anc_id = anc["id"].split("/")[-1]
            if anc_id in ideas:
                parent_id = anc_id
                category = ideas[anc_id].category
                break

        if not category:
            # Try to infer from name
            for root_idea in ideas.values():
                if root_idea.title.lower() in name.lower() or name.lower() in root_idea.title.lower():
                    parent_id = root_idea.id
                    category = root_idea.category
                    break
            if not category:
                category = "General Science"

        desc = detail.get("description") or ""
        ideas[cid] = make_idea(cid, name, desc, 1, category, c.get("works_count", 0))
        l1_added += 1

        if parent_id:
            add_edge(parent_id, cid, "derived_from", 0.85,
                     f"{name} is a direct sub-field of {ideas[parent_id].title}")
            parent_children.setdefault(parent_id, []).append((name, desc))

    print(f"  Added {l1_added} sub-fields")

    # ── LLM enrich level-1 ────────────────────────────────────────────────────
    if LLM_OK:
        print("\n[3/5] LLM enriching sub-field descriptions...")
        enriched = 0
        for parent_id, children in list(parent_children.items())[:12]:
            parent_name = ideas[parent_id].title
            print(f"  Enriching {len(children)} children of {parent_name}...")
            descs = llm_describe(parent_name, children)
            for cid, idea in ideas.items():
                if idea.title in descs:
                    # Rebuild with new description
                    ideas[cid] = make_idea(
                        cid, idea.title, descs[idea.title],
                        list(STAGE_MAP.keys())[list(v[0] for v in STAGE_MAP.values()).index(idea.stage)],
                        idea.category, 0
                    )
                    enriched += 1
            time.sleep(1.0)
        print(f"  Enriched {enriched} descriptions")
    else:
        print("\n[3/5] Skipping LLM (no API key)")

    # ── Level 2: Specializations ──────────────────────────────────────────────
    print("\n[4/5] Fetching specializations (level 2)...")
    l2 = fetch_level(2, 200)
    l2_added = 0

    for c in l2[:80]:
        cid = c["id"].split("/")[-1]
        if cid in ideas:
            continue
        name = c.get("display_name", "")
        time.sleep(0.12)
        detail = fetch_detail(cid)
        if not detail:
            continue

        ancestors = detail.get("ancestors") or []
        # Find closest ancestor we already have (highest level = most specific)
        parent_id = None
        category = "General Science"
        for anc in sorted(ancestors, key=lambda a: a.get("level", 0), reverse=True):
            anc_id = anc["id"].split("/")[-1]
            if anc_id in ideas:
                parent_id = anc_id
                category = ideas[anc_id].category
                break

        desc = detail.get("description") or ""
        ideas[cid] = make_idea(cid, name, desc, 2, category, c.get("works_count", 0))
        l2_added += 1

        if parent_id:
            add_edge(parent_id, cid, "derived_from", 0.80,
                     f"{name} specializes from {ideas[parent_id].title}")

    print(f"  Added {l2_added} specializations. Total: {len(ideas)}")

    # ── Level 3: Modern applications ─────────────────────────────────────────
    print("\n[5/5] Fetching modern applications (level 3)...")
    l3 = fetch_level(3, 100)
    l3_added = 0

    for c in l3[:40]:
        cid = c["id"].split("/")[-1]
        if cid in ideas:
            continue
        name = c.get("display_name", "")
        time.sleep(0.12)
        detail = fetch_detail(cid)
        if not detail:
            continue

        ancestors = detail.get("ancestors") or []
        parent_id = None
        category = "General Science"
        for anc in sorted(ancestors, key=lambda a: a.get("level", 0), reverse=True):
            anc_id = anc["id"].split("/")[-1]
            if anc_id in ideas:
                parent_id = anc_id
                category = ideas[anc_id].category
                break

        desc = detail.get("description") or ""
        ideas[cid] = make_idea(cid, name, desc, 3, category, c.get("works_count", 0))
        l3_added += 1

        if parent_id:
            add_edge(parent_id, cid, "derived_from", 0.75,
                     f"{name} is a modern application of {ideas[parent_id].title}")

    print(f"  Added {l3_added} modern concepts. Total: {len(ideas)}")

    return list(ideas.values()), edges


def save(ideas: List[IdeaNode], edges: List[InfluenceEdge]):
    data_dir = "data/evolution_tracker_api"
    os.makedirs(data_dir, exist_ok=True)

    # Write directly as JSON (overwrites existing files)
    ideas_dict = {idea.id: idea.to_dict() for idea in ideas}
    edges_list = [edge.to_dict() for edge in edges]

    with open(os.path.join(data_dir, "ideas.json"), "w", encoding="utf-8") as f:
        json.dump(ideas_dict, f, indent=2, ensure_ascii=False, default=str)

    with open(os.path.join(data_dir, "edges.json"), "w", encoding="utf-8") as f:
        json.dump(edges_list, f, indent=2, ensure_ascii=False, default=str)

    si, se = len(ideas), len(edges)

    from collections import Counter
    cats = Counter(i.category for i in ideas)

    print(f"\n{'='*60}")
    print(f"DONE: {si} ideas, {se} edges ({se/max(si,1):.1f} avg)")
    print(f"\nTop fields:")
    for cat, cnt in cats.most_common(12):
        print(f"  {cat:<30} {cnt:>3} ideas")

    # Show sample chains
    print(f"\nSample chains to test:")
    for field in ["Chemistry", "Biology", "Physics", "Computer science"]:
        field_ideas = sorted([i for i in ideas if i.category == field], key=lambda x: x.start_year)
        if len(field_ideas) >= 2:
            chain = " -> ".join(i.title for i in field_ideas[:4])
            print(f"  {chain}")

    print(f"\n1. Restart backend: python -m backend.api")
    print(f"2. Refresh browser: Ctrl+Shift+R")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("="*60)
    print("PROPER LINEAGE FETCHER")
    print("Real OpenAlex hierarchy + Gemini LLM enrichment")
    print("="*60)
    ideas, edges = build()
    save(ideas, edges)
