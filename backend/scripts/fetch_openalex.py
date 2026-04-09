import urllib.request
import json
import os
import shutil
import time
from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore

# Known key contributors per concept name (curated fallback)
KNOWN_AUTHORS = {
    "Physics": ["Isaac Newton", "Albert Einstein", "Richard Feynman"],
    "Chemistry": ["Antoine Lavoisier", "Marie Curie", "Linus Pauling"],
    "Biology": ["Charles Darwin", "Gregor Mendel", "Francis Crick"],
    "Mathematics": ["Euclid", "Carl Friedrich Gauss", "Henri Poincaré"],
    "Computer science": ["Alan Turing", "John von Neumann", "Claude Shannon"],
    "Medicine": ["Hippocrates", "Louis Pasteur", "Alexander Fleming"],
    "Economics": ["Adam Smith", "John Maynard Keynes", "Milton Friedman"],
    "Psychology": ["Sigmund Freud", "William James", "Ivan Pavlov"],
    "Quantum mechanics": ["Max Planck", "Niels Bohr", "Werner Heisenberg"],
    "Genetics": ["Gregor Mendel", "James Watson", "Francis Crick"],
    "Thermodynamics": ["James Watt", "Rudolf Clausius", "Lord Kelvin"],
    "Electromagnetism": ["Michael Faraday", "James Clerk Maxwell", "Heinrich Hertz"],
    "Relativity": ["Albert Einstein", "Hendrik Lorentz"],
    "Artificial intelligence": ["Alan Turing", "John McCarthy", "Marvin Minsky"],
    "Machine learning": ["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
    "Neuroscience": ["Santiago Ramón y Cajal", "Charles Sherrington"],
    "Astronomy": ["Galileo Galilei", "Johannes Kepler", "Edwin Hubble"],
    "Optics": ["Ibn al-Haytham", "Isaac Newton", "Christiaan Huygens"],
    "Calculus": ["Isaac Newton", "Gottfried Wilhelm Leibniz"],
    "Statistics": ["Carl Friedrich Gauss", "Ronald Fisher", "Karl Pearson"],
}

def fetch_top_authors_for_concept(concept_id: str, concept_name: str) -> list:
    """Fetch top authors from OpenAlex works for a given concept."""
    # First check curated list
    for key, authors in KNOWN_AUTHORS.items():
        if key.lower() in concept_name.lower() or concept_name.lower() in key.lower():
            return authors

    # Try fetching from OpenAlex works API
    try:
        url = (
            f"https://api.openalex.org/works"
            f"?filter=concepts.id:{concept_id}&sort=cited_by_count:desc"
            f"&per-page=5&select=authorships"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "mailto:test@example.com"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
        authors = []
        for work in data.get("results", []):
            for authorship in work.get("authorships", [])[:2]:
                name = authorship.get("author", {}).get("display_name")
                if name and name not in authors:
                    authors.append(name)
            if len(authors) >= 3:
                break
        return authors if authors else ["Unknown Scholar"]
    except Exception:
        return ["Unknown Scholar"]


def fetch_concepts():
    """Fetch high-impact concepts from OpenAlex."""
    print("Fetching OpenAlex concepts...")
    url = 'https://api.openalex.org/concepts?per-page=200&sort=works_count:desc'
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:test@example.com'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        return data.get('results', [])
    except Exception as e:
        print(f"Error fetching concepts: {e}")
        return []

def map_level_to_stage_and_year(level):
    """Map OpenAlex concept level to EvolutionStage and proxy years."""
    if level == 0:
        return EvolutionStage.PHILOSOPHY, 1800, 1850
    elif level == 1:
        return EvolutionStage.SCIENTIFIC_VALIDATION, 1850, 1950
    elif level == 2:
        return EvolutionStage.ENGINEERING_APPLICATION, 1950, 2000
    else:
        return EvolutionStage.MODERN_TECHNOLOGY, 2000, 2025

def generate_lineage(concepts, store):
    """Generate IdeaNodes and InfluenceEdges and save to DataStore."""
    concept_map = {c['id'].split('/')[-1]: c for c in concepts}
    edges = []

    def get_category(c):
        ancestors = c.get('ancestors') or []
        for anc in ancestors:
            if anc.get('level') == 0:
                return anc.get('display_name')
        return "General Science"

    max_score = max((c.get('works_count', 1) for c in concepts), default=1)

    for idx, c in enumerate(concepts):
        c_id = c['id'].split('/')[-1]
        level = c.get('level', 0)
        name = c.get('display_name', '')

        stage, start_y, end_y = map_level_to_stage_and_year(level)
        category = name if level == 0 else get_category(c)
        score = c.get('works_count', 0) / max_score

        # Get real author names
        authors = fetch_top_authors_for_concept(c_id, name)
        print(f"  [{idx+1}/{len(concepts)}] {name} → {authors}")

        idea = IdeaNode(
            id=c_id,
            title=name[:100],
            description=c.get('description') or f"Concept of {name}",
            stage=stage,
            start_year=start_y,
            end_year=end_y,
            category=category,
            laureates=authors,
            motivation=f"Scholarly significance with {c.get('works_count', 0):,} works.",
            keywords=[name.lower()],
            influence_score=round(max(0.1, score), 4)
        )
        try:
            store.add_idea(idea)
        except ValueError:
            pass  # skip duplicates

        # Ancestor edges
        for anc in (c.get('ancestors') or []):
            anc_id = anc['id'].split('/')[-1]
            if anc_id in concept_map and anc_id != c_id:
                edges.append(InfluenceEdge(
                    source_id=anc_id, target_id=c_id,
                    influence_type="derived_from",
                    influence_weight=0.8,
                    evidence="OpenAlex Ancestry",
                    confidence_score=0.9
                ))

        # Related edges
        for rel in (c.get('related_concepts') or [])[:3]:
            rel_id = rel['id'].split('/')[-1]
            if rel_id in concept_map and rel_id != c_id:
                edges.append(InfluenceEdge(
                    source_id=rel_id, target_id=c_id,
                    influence_type="inspired_by",
                    influence_weight=0.5,
                    evidence="OpenAlex Related",
                    confidence_score=0.6
                ))

    for edge in edges:
        try:
            store.add_edge(edge)
        except Exception:
            pass

    print(f"\n✅ Imported {len(concepts)} concepts with real author names and {len(edges)} edges.")

def main():
    print("🧹 Cleaning existing dataset...")
    data_dir = "data/evolution_tracker_api"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)
        time.sleep(1)
    os.makedirs(data_dir, exist_ok=True)
    store = DataStore(data_dir=data_dir)
    concepts = fetch_concepts()
    if not concepts:
        print("Failed to fetch concepts. Aborting.")
        return
    generate_lineage(concepts, store)
    print("✅ Dataset ready. Start the API with: python -m backend.api")

if __name__ == "__main__":
    main()
