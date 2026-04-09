"""Re-categorize ideas with meaningful categories based on their titles and keywords."""
import json

CATEGORY_RULES = {
    "Quantum Physics": ["quantum", "qubit", "entanglement", "superposition", "planck"],
    "Nuclear Physics": ["nuclear", "fission", "fusion", "radioactive", "atomic", "neutron", "proton", "isotope"],
    "Particle Physics": ["particle", "boson", "fermion", "hadron", "lepton", "quark", "higgs", "collider"],
    "Astrophysics": ["cosmic", "galaxy", "star", "pulsar", "nebula", "dark matter", "dark energy", "gravitational wave", "black hole", "supernova", "exoplanet"],
    "Classical Physics": ["mechanics", "thermodynamics", "electromagnetism", "optics", "acoustics", "fluid"],
    "Computer Science": ["computer", "algorithm", "software", "programming", "artificial intelligence", "machine learning", "neural network", "data structure", "computation", "turing", "compiler"],
    "Mathematics": ["mathematics", "algebra", "geometry", "calculus", "topology", "statistics", "probability", "number theory", "combinatorics"],
    "Chemistry": ["chemistry", "chemical", "molecule", "polymer", "catalyst", "reaction", "compound", "organic", "inorganic", "electrochemistry"],
    "Biology": ["biology", "cell", "gene", "dna", "rna", "protein", "evolution", "ecology", "organism", "microbiology", "genetics", "enzyme"],
    "Medicine": ["medicine", "disease", "drug", "therapy", "vaccine", "pathology", "clinical", "pharmaceutical", "surgery", "diagnosis", "immunology"],
    "Neuroscience": ["brain", "neuron", "cognitive", "neuroscience", "synapse", "consciousness", "neural"],
    "Materials Science": ["material", "semiconductor", "crystal", "alloy", "ceramic", "composite", "nanotechnology", "graphene"],
    "Engineering": ["engineering", "circuit", "robot", "sensor", "manufacturing", "mechanical", "electrical", "signal processing"],
    "Environmental Science": ["climate", "environment", "pollution", "ecosystem", "sustainability", "renewable", "greenhouse", "biodiversity"],
    "Earth Science": ["geology", "seismology", "oceanography", "atmosphere", "mineral", "plate tectonic", "volcano", "earthquake"],
    "Economics": ["economics", "market", "trade", "finance", "monetary", "fiscal", "gdp", "inflation"],
    "Political Science": ["political", "governance", "democracy", "policy", "legislation", "diplomacy"],
    "Philosophy": ["philosophy", "epistemology", "metaphysics", "ethics", "ontology", "logic", "phenomenology"],
    "Information Science": ["information", "data", "network", "internet", "communication", "signal", "database", "web"],
    "Biotechnology": ["biotechnology", "crispr", "cloning", "bioinformatics", "genomics", "proteomics", "synthetic biology"],
}

def categorize(title, keywords, current_cat):
    """Assign best category based on title and keywords."""
    if current_cat != "General Science":
        return current_cat

    text = (title + " " + " ".join(keywords)).lower()
    best_cat = None
    best_score = 0

    for cat, terms in CATEGORY_RULES.items():
        score = sum(1 for t in terms if t in text)
        if score > best_score:
            best_score = score
            best_cat = cat

    return best_cat if best_cat else current_cat

def main():
    path = "data/evolution_tracker_api/ideas.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    cat_counts = {}
    for idea_id, idea in data.items():
        old_cat = idea["category"]
        new_cat = categorize(idea["title"], idea.get("keywords", []), old_cat)
        if new_cat != old_cat:
            idea["category"] = new_cat
            changed += 1
        cat_counts[idea["category"]] = cat_counts.get(idea["category"], 0) + 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Re-categorized {changed} ideas")
    print(f"\nCategory Distribution ({len(cat_counts)} categories):")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()
