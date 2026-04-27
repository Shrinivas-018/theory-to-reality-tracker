import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATA_DIR = "data/evolution_tracker_api"

# Real scientific parent -> children relationships
HIERARCHY = [
    ("Chemistry", "Organic chemistry"), ("Chemistry", "Inorganic chemistry"),
    ("Chemistry", "Physical chemistry"), ("Chemistry", "Analytical chemistry"),
    ("Chemistry", "Biochemistry"), ("Chemistry", "Polymer chemistry"),
    ("Chemistry", "Nuclear chemistry"), ("Chemistry", "Electrochemistry"),
    ("Chemistry", "Environmental chemistry"), ("Chemistry", "Computational chemistry"),
    ("Organic chemistry", "Biochemistry"), ("Organic chemistry", "Medicinal chemistry"),
    ("Organic chemistry", "Polymer chemistry"), ("Organic chemistry", "Stereochemistry"),
    ("Biochemistry", "Molecular biology"), ("Biochemistry", "Enzymology"),
    ("Biochemistry", "Metabolomics"), ("Biochemistry", "Proteomics"),
    ("Molecular biology", "Genomics"), ("Molecular biology", "Proteomics"),
    ("Molecular biology", "Bioinformatics"), ("Molecular biology", "Cell biology"),
    ("Genomics", "Bioinformatics"), ("Genomics", "Epigenomics"),
    ("Biology", "Genetics"), ("Biology", "Ecology"),
    ("Biology", "Evolutionary biology"), ("Biology", "Cell biology"),
    ("Biology", "Microbiology"), ("Biology", "Botany"),
    ("Biology", "Zoology"), ("Biology", "Physiology"),
    ("Biology", "Neuroscience"), ("Biology", "Immunology"),
    ("Genetics", "Molecular biology"), ("Genetics", "Genomics"),
    ("Genetics", "Population genetics"),
    ("Cell biology", "Molecular biology"), ("Cell biology", "Microbiology"),
    ("Evolutionary biology", "Genetics"), ("Evolutionary biology", "Ecology"),
    ("Evolutionary biology", "Paleontology"),
    ("Microbiology", "Virology"), ("Microbiology", "Immunology"),
    ("Neuroscience", "Cognitive science"), ("Neuroscience", "Psychiatry"),
    ("Neuroscience", "Neurology"),
    ("Immunology", "Pharmacology"), ("Immunology", "Virology"),
    ("Physics", "Quantum mechanics"), ("Physics", "Thermodynamics"),
    ("Physics", "Electromagnetism"), ("Physics", "Optics"),
    ("Physics", "Nuclear physics"), ("Physics", "Astrophysics"),
    ("Physics", "Mechanics"), ("Physics", "Condensed matter physics"),
    ("Physics", "Atomic physics"),
    ("Quantum mechanics", "Particle physics"), ("Quantum mechanics", "Quantum computing"),
    ("Quantum mechanics", "Condensed matter physics"), ("Quantum mechanics", "Quantum optics"),
    ("Electromagnetism", "Optics"), ("Electromagnetism", "Electronics"),
    ("Electromagnetism", "Photonics"),
    ("Optics", "Photonics"), ("Optics", "Spectroscopy"),
    ("Nuclear physics", "Particle physics"), ("Nuclear physics", "Nuclear engineering"),
    ("Nuclear physics", "Astrophysics"),
    ("Thermodynamics", "Statistical mechanics"), ("Thermodynamics", "Chemical engineering"),
    ("Condensed matter physics", "Materials science"), ("Condensed matter physics", "Nanotechnology"),
    ("Atomic physics", "Nuclear physics"),
    ("Computer science", "Artificial intelligence"), ("Computer science", "Algorithms"),
    ("Computer science", "Programming language"), ("Computer science", "Database"),
    ("Computer science", "Computer vision"), ("Computer science", "Cryptography"),
    ("Computer science", "Operating system"), ("Computer science", "Software engineering"),
    ("Artificial intelligence", "Machine learning"), ("Artificial intelligence", "Natural language processing"),
    ("Artificial intelligence", "Computer vision"), ("Artificial intelligence", "Robotics"),
    ("Machine learning", "Deep learning"), ("Machine learning", "Reinforcement learning"),
    ("Machine learning", "Neural network"), ("Machine learning", "Computer vision"),
    ("Deep learning", "Computer vision"), ("Deep learning", "Natural language processing"),
    ("Natural language processing", "Computational linguistics"), ("Natural language processing", "Information retrieval"),
    ("Database", "Data mining"), ("Database", "Information retrieval"),
    ("Algorithms", "Cryptography"), ("Algorithms", "Data structure"),
    ("Mathematics", "Algebra"), ("Mathematics", "Calculus"),
    ("Mathematics", "Statistics"), ("Mathematics", "Geometry"),
    ("Mathematics", "Number theory"), ("Mathematics", "Topology"),
    ("Mathematics", "Mathematical analysis"), ("Mathematics", "Combinatorics"),
    ("Mathematics", "Probability theory"),
    ("Calculus", "Mathematical analysis"), ("Calculus", "Differential equations"),
    ("Statistics", "Probability theory"), ("Statistics", "Biostatistics"),
    ("Algebra", "Number theory"), ("Algebra", "Linear algebra"),
    ("Geometry", "Topology"), ("Geometry", "Differential geometry"),
    ("Medicine", "Pharmacology"), ("Medicine", "Surgery"),
    ("Medicine", "Pathology"), ("Medicine", "Immunology"),
    ("Medicine", "Cardiology"), ("Medicine", "Oncology"),
    ("Medicine", "Neurology"), ("Medicine", "Psychiatry"),
    ("Medicine", "Radiology"), ("Medicine", "Epidemiology"),
    ("Medicine", "Internal medicine"),
    ("Pharmacology", "Toxicology"), ("Pharmacology", "Drug discovery"),
    ("Oncology", "Immunology"), ("Oncology", "Genomics"), ("Oncology", "Radiology"),
    ("Cardiology", "Internal medicine"), ("Cardiology", "Surgery"),
    ("Psychiatry", "Neuroscience"), ("Psychiatry", "Pharmacology"),
    ("Epidemiology", "Statistics"),
    ("Engineering", "Electrical engineering"), ("Engineering", "Mechanical engineering"),
    ("Engineering", "Chemical engineering"), ("Engineering", "Civil engineering"),
    ("Engineering", "Nuclear engineering"), ("Engineering", "Biomedical engineering"),
    ("Engineering", "Computer engineering"), ("Engineering", "Materials science"),
    ("Electrical engineering", "Electronics"), ("Electrical engineering", "Telecommunications"),
    ("Electrical engineering", "Computer engineering"), ("Electrical engineering", "Signal processing"),
    ("Mechanical engineering", "Thermodynamics"), ("Mechanical engineering", "Fluid mechanics"),
    ("Mechanical engineering", "Robotics"),
    ("Chemical engineering", "Biochemistry"), ("Chemical engineering", "Materials science"),
    ("Chemical engineering", "Thermodynamics"),
    ("Biomedical engineering", "Medicine"), ("Biomedical engineering", "Materials science"),
    ("Materials science", "Nanotechnology"), ("Materials science", "Polymer chemistry"),
    ("Materials science", "Metallurgy"), ("Materials science", "Crystallography"),
    ("Economics", "Finance"), ("Economics", "Econometrics"),
    ("Economics", "Microeconomics"), ("Economics", "Macroeconomics"),
    ("Economics", "Behavioral economics"),
    ("Finance", "Statistics"), ("Econometrics", "Statistics"),
    ("Psychology", "Cognitive science"), ("Psychology", "Social psychology"),
    ("Psychology", "Neuroscience"), ("Psychology", "Behavioral economics"),
    ("Psychology", "Psychiatry"),
    ("Cognitive science", "Neuroscience"), ("Cognitive science", "Artificial intelligence"),
    ("Cognitive science", "Linguistics"),
    # Cross-domain
    ("Bioinformatics", "Computer science"), ("Bioinformatics", "Statistics"),
    ("Quantum computing", "Computer science"), ("Quantum computing", "Algorithms"),
    ("Nanotechnology", "Physics"), ("Nanotechnology", "Chemistry"),
    ("Robotics", "Mechanical engineering"), ("Robotics", "Artificial intelligence"),
    ("Computational chemistry", "Chemistry"), ("Computational chemistry", "Computer science"),
]


def main():
    with open(os.path.join(DATA_DIR, "ideas.json"), "r", encoding="utf-8") as f:
        ideas = json.load(f)

    print(f"Loaded {len(ideas)} ideas")

    # Build title -> id map (case-insensitive)
    title_to_id = {idea.get("title", "").strip().lower(): cid for cid, idea in ideas.items()}
    print(f"Title index: {len(title_to_id)} entries")

    edges = []
    edge_set = set()
    matched = 0
    missed = []

    for parent_title, child_title in HIERARCHY:
        parent_id = title_to_id.get(parent_title.lower())
        child_id = title_to_id.get(child_title.lower())

        if parent_id and child_id:
            key = (parent_id, child_id)
            if key not in edge_set:
                edge_set.add(key)
                edges.append({
                    "source_id": parent_id,
                    "target_id": child_id,
                    "influence_type": "derived_from",
                    "influence_weight": 0.85,
                    "evidence": f"{child_title} is a sub-field of {parent_title}",
                    "confidence_score": 0.95,
                    "created_at": "2026-04-23T00:00:00"
                })
                matched += 1
        else:
            if not parent_id:
                missed.append(f"PARENT missing: {parent_title}")
            if not child_id:
                missed.append(f"CHILD missing: {child_title}")

    print(f"\nMatched: {matched} edges")
    print(f"Missed: {len(missed)} (concepts not in our dataset)")

    if missed[:10]:
        print("\nSample missing:")
        for m in missed[:10]:
            print(f"  {m}")

    # Show what we got
    print(f"\nSample edges built:")
    for e in edges[:20]:
        src = ideas.get(e["source_id"], {}).get("title", "?")
        tgt = ideas.get(e["target_id"], {}).get("title", "?")
        print(f"  {src} -> {tgt}")

    # Save
    with open(os.path.join(DATA_DIR, "edges.json"), "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(edges)} edges")
    print("Restart backend: python -m backend.api")
    print("\nTest these paths:")
    print("  Chemistry -> Organic chemistry -> Biochemistry -> Molecular biology -> Genomics")
    print("  Physics -> Quantum mechanics -> Particle physics")
    print("  Computer science -> Artificial intelligence -> Machine learning -> Deep learning")
    print("  Biology -> Genetics -> Molecular biology -> Bioinformatics")


if __name__ == "__main__":
    main()
