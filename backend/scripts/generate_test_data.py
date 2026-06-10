"""
Generate comprehensive test data for tree map visualization testing.

Creates multiple evolution chains with rich interconnections:
- Computer Science evolution chain (10 ideas)
- Physics evolution chain (8 ideas)
- Biology evolution chain (8 ideas)
- Cross-domain connections between chains
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage


def generate_test_data():
    """Generate rich test data with multiple evolution chains."""
    
    ideas = []
    edges = []
    
    # ═══════════════════════════════════════════════════════════
    # COMPUTER SCIENCE EVOLUTION CHAIN
    # ═══════════════════════════════════════════════════════════
    
    cs_chain = [
        {
            "id": "CS001",
            "title": "Mathematical Logic",
            "description": "Foundational work in formal logic and mathematical reasoning by George Boole and others, establishing the basis for computational thinking.",
            "stage": EvolutionStage.PHILOSOPHY,
            "start_year": 1850,
            "end_year": 1900,
            "category": "Computer Science",
            "laureates": ["George Boole", "Gottlob Frege", "Giuseppe Peano"],
            "motivation": "Foundational work in formal logic",
            "keywords": ["logic", "boolean algebra", "formal systems"],
            "influence_score": 0.85,
        },
        {
            "id": "CS002",
            "title": "Turing Machine",
            "description": "Alan Turing's theoretical model of computation that defined what it means for a problem to be computable.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1936,
            "end_year": 1950,
            "category": "Computer Science",
            "laureates": ["Alan Turing", "Alonzo Church"],
            "keywords": ["computation", "algorithms", "decidability"],
            "influence_score": 0.95,
        },
        {
            "id": "CS003",
            "title": "Stored-Program Computer",
            "description": "Von Neumann architecture enabling computers to store programs in memory alongside data, revolutionizing computing.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1945,
            "end_year": 1960,
            "category": "Computer Science",
            "laureates": ["John von Neumann", "J. Presper Eckert", "John Mauchly"],
            "keywords": ["architecture", "memory", "programming"],
            "influence_score": 0.92,
        },
        {
            "id": "CS004",
            "title": "High-Level Programming Languages",
            "description": "Development of FORTRAN, COBOL, and other languages that abstracted away machine code, making programming accessible.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1957,
            "end_year": 1970,
            "category": "Computer Science",
            "laureates": ["John Backus", "Grace Hopper", "John McCarthy"],
            "keywords": ["programming", "compilers", "abstraction"],
            "influence_score": 0.88,
        },
        {
            "id": "CS005",
            "title": "Operating Systems",
            "description": "UNIX and other operating systems that managed computer resources and provided interfaces for applications.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1969,
            "end_year": 1985,
            "category": "Computer Science",
            "laureates": ["Ken Thompson", "Dennis Ritchie", "Linus Torvalds"],
            "keywords": ["OS", "kernel", "multitasking"],
            "influence_score": 0.90,
        },
        {
            "id": "CS006",
            "title": "Relational Databases",
            "description": "Edgar Codd's relational model revolutionized data storage and retrieval with SQL and ACID properties.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1970,
            "end_year": 1990,
            "category": "Computer Science",
            "laureates": ["Edgar F. Codd", "Michael Stonebraker", "Jim Gray"],
            "keywords": ["databases", "SQL", "data management"],
            "influence_score": 0.87,
        },
        {
            "id": "CS007",
            "title": "Internet Protocol Suite",
            "description": "TCP/IP protocols enabling global computer networking and the foundation of the modern internet.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1974,
            "end_year": 1995,
            "category": "Computer Science",
            "laureates": ["Vint Cerf", "Bob Kahn", "Tim Berners-Lee"],
            "keywords": ["networking", "TCP/IP", "internet"],
            "influence_score": 0.98,
        },
        {
            "id": "CS008",
            "title": "Machine Learning",
            "description": "Algorithms that enable computers to learn from data without explicit programming, including neural networks.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1980,
            "end_year": 2010,
            "category": "Computer Science",
            "laureates": ["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
            "keywords": ["AI", "neural networks", "deep learning"],
            "influence_score": 0.96,
        },
        {
            "id": "CS009",
            "title": "Cloud Computing",
            "description": "On-demand computing resources delivered over the internet, enabling scalable and flexible infrastructure.",
            "stage": EvolutionStage.MODERN_TECHNOLOGY,
            "start_year": 2006,
            "end_year": 2020,
            "category": "Computer Science",
            "laureates": ["Werner Vogels", "Eric Schmidt", "Satya Nadella"],
            "keywords": ["cloud", "AWS", "distributed systems"],
            "influence_score": 0.94,
        },
        {
            "id": "CS010",
            "title": "Large Language Models",
            "description": "Transformer-based AI models capable of understanding and generating human-like text at scale.",
            "stage": EvolutionStage.MODERN_TECHNOLOGY,
            "start_year": 2017,
            "end_year": 2024,
            "category": "Computer Science",
            "laureates": ["Ashish Vaswani", "Ilya Sutskever", "Demis Hassabis"],
            "keywords": ["transformers", "GPT", "NLP"],
            "influence_score": 1.0,
        },
    ]
    
    # ═══════════════════════════════════════════════════════════
    # PHYSICS EVOLUTION CHAIN
    # ═══════════════════════════════════════════════════════════
    
    physics_chain = [
        {
            "id": "PHY001",
            "title": "Classical Mechanics",
            "description": "Newton's laws of motion and universal gravitation, forming the foundation of classical physics.",
            "stage": EvolutionStage.PHILOSOPHY,
            "start_year": 1800,
            "end_year": 1850,
            "category": "Physics",
            "laureates": ["Isaac Newton", "Leonhard Euler", "Joseph-Louis Lagrange"],
            "keywords": ["mechanics", "gravity", "motion"],
            "influence_score": 0.90,
        },
        {
            "id": "PHY002",
            "title": "Thermodynamics",
            "description": "Laws governing heat, energy, and entropy in physical systems.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1824,
            "end_year": 1900,
            "category": "Physics",
            "laureates": ["Sadi Carnot", "Rudolf Clausius", "Ludwig Boltzmann"],
            "keywords": ["heat", "entropy", "energy"],
            "influence_score": 0.86,
        },
        {
            "id": "PHY003",
            "title": "Electromagnetism",
            "description": "Maxwell's equations unifying electricity and magnetism into a single electromagnetic force.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1861,
            "end_year": 1900,
            "category": "Physics",
            "laureates": ["James Clerk Maxwell", "Michael Faraday", "Heinrich Hertz"],
            "keywords": ["electromagnetism", "waves", "light"],
            "influence_score": 0.92,
        },
        {
            "id": "PHY004",
            "title": "Quantum Mechanics",
            "description": "Revolutionary theory describing the behavior of matter and energy at atomic and subatomic scales.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1900,
            "end_year": 1930,
            "category": "Physics",
            "laureates": ["Max Planck", "Niels Bohr", "Werner Heisenberg"],
            "keywords": ["quantum", "wave-particle duality", "uncertainty"],
            "influence_score": 0.98,
        },
        {
            "id": "PHY005",
            "title": "Nuclear Physics",
            "description": "Study of atomic nuclei, radioactivity, and nuclear reactions enabling both energy and weapons.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1932,
            "end_year": 1960,
            "category": "Physics",
            "laureates": ["Ernest Rutherford", "Enrico Fermi", "J. Robert Oppenheimer"],
            "keywords": ["nuclear", "fission", "radioactivity"],
            "influence_score": 0.89,
        },
        {
            "id": "PHY006",
            "title": "Semiconductor Physics",
            "description": "Understanding of semiconductor materials enabling transistors and integrated circuits.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1947,
            "end_year": 1970,
            "category": "Physics",
            "laureates": ["William Shockley", "John Bardeen", "Walter Brattain"],
            "keywords": ["semiconductors", "transistors", "electronics"],
            "influence_score": 0.95,
        },
        {
            "id": "PHY007",
            "title": "Laser Technology",
            "description": "Light amplification by stimulated emission of radiation, enabling precision tools and communications.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1960,
            "end_year": 1990,
            "category": "Physics",
            "laureates": ["Theodore Maiman", "Charles Townes", "Arthur Schawlow"],
            "keywords": ["laser", "optics", "photonics"],
            "influence_score": 0.88,
        },
        {
            "id": "PHY008",
            "title": "Quantum Computing",
            "description": "Computing paradigm using quantum superposition and entanglement for exponential speedups.",
            "stage": EvolutionStage.MODERN_TECHNOLOGY,
            "start_year": 1994,
            "end_year": 2024,
            "category": "Physics",
            "laureates": ["Peter Shor", "David Deutsch", "John Preskill"],
            "keywords": ["quantum computing", "qubits", "superposition"],
            "influence_score": 0.93,
        },
    ]
    
    # ═══════════════════════════════════════════════════════════
    # BIOLOGY EVOLUTION CHAIN
    # ═══════════════════════════════════════════════════════════
    
    biology_chain = [
        {
            "id": "BIO001",
            "title": "Cell Theory",
            "description": "Discovery that all living organisms are composed of cells, the fundamental unit of life.",
            "stage": EvolutionStage.PHILOSOPHY,
            "start_year": 1838,
            "end_year": 1880,
            "category": "Biology",
            "laureates": ["Matthias Schleiden", "Theodor Schwann", "Rudolf Virchow"],
            "keywords": ["cells", "microscopy", "life"],
            "influence_score": 0.87,
        },
        {
            "id": "BIO002",
            "title": "Evolution by Natural Selection",
            "description": "Darwin's theory explaining how species evolve through differential survival and reproduction.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1859,
            "end_year": 1900,
            "category": "Biology",
            "laureates": ["Charles Darwin", "Alfred Russel Wallace"],
            "keywords": ["evolution", "natural selection", "adaptation"],
            "influence_score": 0.96,
        },
        {
            "id": "BIO003",
            "title": "Mendelian Genetics",
            "description": "Gregor Mendel's laws of inheritance explaining how traits are passed from parents to offspring.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1866,
            "end_year": 1920,
            "category": "Biology",
            "laureates": ["Gregor Mendel", "Thomas Hunt Morgan"],
            "keywords": ["genetics", "inheritance", "genes"],
            "influence_score": 0.91,
        },
        {
            "id": "BIO004",
            "title": "DNA Structure",
            "description": "Discovery of the double helix structure of DNA, revealing how genetic information is stored.",
            "stage": EvolutionStage.SCIENTIFIC_VALIDATION,
            "start_year": 1953,
            "end_year": 1970,
            "category": "Biology",
            "laureates": ["James Watson", "Francis Crick", "Rosalind Franklin"],
            "keywords": ["DNA", "double helix", "molecular biology"],
            "influence_score": 0.99,
        },
        {
            "id": "BIO005",
            "title": "Genetic Engineering",
            "description": "Techniques for directly manipulating DNA, enabling creation of GMOs and gene therapy.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1973,
            "end_year": 1995,
            "category": "Biology",
            "laureates": ["Paul Berg", "Herbert Boyer", "Stanley Cohen"],
            "keywords": ["genetic engineering", "recombinant DNA", "biotechnology"],
            "influence_score": 0.90,
        },
        {
            "id": "BIO006",
            "title": "Human Genome Project",
            "description": "Complete sequencing of human DNA, mapping all ~20,000 genes in the human genome.",
            "stage": EvolutionStage.ENGINEERING_APPLICATION,
            "start_year": 1990,
            "end_year": 2003,
            "category": "Biology",
            "laureates": ["Francis Collins", "Craig Venter", "Eric Lander"],
            "keywords": ["genomics", "sequencing", "human genome"],
            "influence_score": 0.94,
        },
        {
            "id": "BIO007",
            "title": "CRISPR Gene Editing",
            "description": "Precise gene editing technology enabling targeted modifications to DNA sequences.",
            "stage": EvolutionStage.MODERN_TECHNOLOGY,
            "start_year": 2012,
            "end_year": 2020,
            "category": "Biology",
            "laureates": ["Jennifer Doudna", "Emmanuelle Charpentier", "Feng Zhang"],
            "keywords": ["CRISPR", "gene editing", "Cas9"],
            "influence_score": 0.97,
        },
        {
            "id": "BIO008",
            "title": "Synthetic Biology",
            "description": "Engineering biological systems and organisms with novel functions not found in nature.",
            "stage": EvolutionStage.MODERN_TECHNOLOGY,
            "start_year": 2010,
            "end_year": 2024,
            "category": "Biology",
            "laureates": ["George Church", "Drew Endy", "Jay Keasling"],
            "keywords": ["synthetic biology", "bioengineering", "designer organisms"],
            "influence_score": 0.89,
        },
    ]
    
    # Combine all ideas
    all_ideas = cs_chain + physics_chain + biology_chain
    
    # Convert to IdeaNode objects
    for idea_data in all_ideas:
        # Add motivation if not present
        if "motivation" not in idea_data:
            idea_data["motivation"] = f"Significant contribution to {idea_data['category']}"
        idea = IdeaNode(**idea_data)
        ideas.append(idea)
    
    # ═══════════════════════════════════════════════════════════
    # GENERATE EDGES - LINEAR CHAINS
    # ═══════════════════════════════════════════════════════════
    
    # Computer Science chain
    for i in range(len(cs_chain) - 1):
        edge = InfluenceEdge(
            source_id=cs_chain[i]["id"],
            target_id=cs_chain[i + 1]["id"],
            influence_type="derived_from",
            influence_weight=0.85 + (i * 0.01),
            evidence=f"Direct evolution from {cs_chain[i]['title']} to {cs_chain[i+1]['title']}",
            confidence_score=0.9,
        )
        edges.append(edge)
    
    # Physics chain
    for i in range(len(physics_chain) - 1):
        edge = InfluenceEdge(
            source_id=physics_chain[i]["id"],
            target_id=physics_chain[i + 1]["id"],
            influence_type="derived_from",
            influence_weight=0.82 + (i * 0.01),
            evidence=f"Direct evolution from {physics_chain[i]['title']} to {physics_chain[i+1]['title']}",
            confidence_score=0.88,
        )
        edges.append(edge)
    
    # Biology chain
    for i in range(len(biology_chain) - 1):
        edge = InfluenceEdge(
            source_id=biology_chain[i]["id"],
            target_id=biology_chain[i + 1]["id"],
            influence_type="derived_from",
            influence_weight=0.80 + (i * 0.01),
            evidence=f"Direct evolution from {biology_chain[i]['title']} to {biology_chain[i+1]['title']}",
            confidence_score=0.87,
        )
        edges.append(edge)
    
    # ═══════════════════════════════════════════════════════════
    # CROSS-DOMAIN CONNECTIONS
    # ═══════════════════════════════════════════════════════════
    
    cross_domain_edges = [
        # Physics → Computer Science
        ("PHY006", "CS003", "applied_to", 0.92, "Semiconductors enabled modern computer hardware"),
        ("PHY004", "CS008", "inspired_by", 0.78, "Quantum mechanics inspired quantum computing concepts"),
        ("PHY008", "CS010", "inspired_by", 0.65, "Quantum computing research influenced AI architectures"),
        
        # Biology → Computer Science
        ("BIO002", "CS008", "inspired_by", 0.72, "Evolution inspired genetic algorithms and neural networks"),
        ("BIO004", "CS006", "inspired_by", 0.68, "DNA structure inspired data storage concepts"),
        ("BIO006", "CS008", "applied_to", 0.81, "Genome sequencing required machine learning for analysis"),
        
        # Computer Science → Biology
        ("CS008", "BIO007", "applied_to", 0.88, "Machine learning accelerated CRISPR target identification"),
        ("CS004", "BIO005", "applied_to", 0.75, "Programming concepts applied to genetic engineering"),
        ("CS009", "BIO008", "applied_to", 0.79, "Cloud computing enables large-scale synthetic biology simulations"),
        
        # Physics → Biology
        ("PHY003", "BIO001", "applied_to", 0.70, "Electromagnetic theory enabled advanced microscopy"),
        ("PHY007", "BIO006", "applied_to", 0.84, "Laser technology enabled DNA sequencing"),
    ]
    
    for source, target, inf_type, weight, evidence in cross_domain_edges:
        edge = InfluenceEdge(
            source_id=source,
            target_id=target,
            influence_type=inf_type,
            influence_weight=weight,
            evidence=evidence,
            confidence_score=0.85,
        )
        edges.append(edge)
    
    return ideas, edges


def save_test_data(ideas, edges, output_dir="data/evolution_tracker_api"):
    """Save generated test data to JSON files."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert ideas to dict
    ideas_dict = {idea.id: idea.to_dict() for idea in ideas}
    
    # Convert edges to list of dicts
    edges_list = [edge.to_dict() for edge in edges]
    
    # Save ideas
    ideas_file = output_path / "ideas.json"
    with open(ideas_file, "w", encoding="utf-8") as f:
        json.dump(ideas_dict, f, indent=2, ensure_ascii=False)
    
    # Save edges
    edges_file = output_path / "edges.json"
    with open(edges_file, "w", encoding="utf-8") as f:
        json.dump(edges_list, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated {len(ideas)} ideas")
    print(f"✅ Generated {len(edges)} edges")
    print(f"✅ Saved to {output_dir}/")
    print()
    print("📊 Summary:")
    print(f"   - Computer Science chain: 10 ideas")
    print(f"   - Physics chain: 8 ideas")
    print(f"   - Biology chain: 8 ideas")
    print(f"   - Linear chain edges: {len(ideas) - 3}")
    print(f"   - Cross-domain edges: {len(edges) - (len(ideas) - 3)}")
    print()
    print("🎯 Test these ideas for tree map visualization:")
    print("   - CS005 (Operating Systems) - middle of CS chain")
    print("   - PHY004 (Quantum Mechanics) - middle of Physics chain")
    print("   - BIO004 (DNA Structure) - middle of Biology chain")
    print("   - CS008 (Machine Learning) - has cross-domain connections")
    print("   - PHY006 (Semiconductor Physics) - connects to CS")
    print("   - BIO006 (Human Genome Project) - connects to CS")


if __name__ == "__main__":
    print("🔬 Generating comprehensive test data...")
    print()
    
    ideas, edges = generate_test_data()
    save_test_data(ideas, edges)
    
    print()
    print("🚀 Next steps:")
    print("   1. Restart the backend server: python -m backend.api")
    print("   2. Refresh the frontend in your browser")
    print("   3. Click on any idea to see the tree map visualization")
