"""
Intelligent OpenAlex Data Fetcher with LLM Enhancement

This script:
1. Fetches concepts from OpenAlex
2. Uses LLM (Gemini) to analyze and create meaningful evolution chains
3. Generates high-quality ancestor/descendant relationships
4. Optimizes data for performance (limits to 200 ideas, smart edge generation)
5. Creates rich, interconnected knowledge graph
"""

import urllib.request
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore

# Check for Gemini API key
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        LLM_AVAILABLE = True
        print("✅ Gemini LLM available for intelligent edge generation")
    else:
        LLM_AVAILABLE = False
        print("⚠️  GEMINI_API_KEY not found. Using rule-based edge generation.")
        print("   Get a free key at: https://aistudio.google.com/")
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Using rule-based edge generation.")
    print("   Install with: pip install google-generativeai")


# Curated author database
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
    "Machine learning": ["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
    "Artificial intelligence": ["Alan Turing", "John McCarthy", "Marvin Minsky"],
}


def fetch_concepts(max_concepts: int = 200) -> List[Dict]:
    """Fetch high-impact concepts from OpenAlex."""
    print(f"\n📡 Fetching top {max_concepts} concepts from OpenAlex...")
    
    # Fetch in batches to respect rate limits
    all_concepts = []
    per_page = 100
    pages = (max_concepts + per_page - 1) // per_page
    
    for page in range(pages):
        url = f'https://api.openalex.org/concepts?per-page={per_page}&page={page+1}&sort=works_count:desc'
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:research@example.com'})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                concepts = data.get('results', [])
                all_concepts.extend(concepts)
                print(f"   Fetched page {page+1}/{pages}: {len(concepts)} concepts")
                
                # Rate limiting
                if page < pages - 1:
                    time.sleep(0.2)  # 5 requests per second
                    
        except Exception as e:
            print(f"   ⚠️  Error fetching page {page+1}: {e}")
            break
    
    # Limit to requested amount
    all_concepts = all_concepts[:max_concepts]
    print(f"✅ Fetched {len(all_concepts)} concepts total\n")
    return all_concepts


def get_authors_for_concept(concept_id: str, concept_name: str) -> List[str]:
    """Get author names for a concept."""
    # Check curated list first
    for key, authors in KNOWN_AUTHORS.items():
        if key.lower() in concept_name.lower():
            return authors
    
    # Default fallback
    return ["Notable Researchers"]


def map_level_to_stage_and_year(level: int) -> Tuple[EvolutionStage, int, int]:
    """Map OpenAlex concept level to evolution stage and years."""
    if level == 0:
        return EvolutionStage.PHILOSOPHY, 1800, 1850
    elif level == 1:
        return EvolutionStage.SCIENTIFIC_VALIDATION, 1850, 1950
    elif level == 2:
        return EvolutionStage.ENGINEERING_APPLICATION, 1950, 2000
    else:
        return EvolutionStage.MODERN_TECHNOLOGY, 2000, 2025


def get_category(concept: Dict) -> str:
    """Extract category from concept ancestors."""
    ancestors = concept.get('ancestors') or []
    for anc in ancestors:
        if anc and anc.get('level') == 0:
            return anc.get('display_name', 'General Science')
    return concept.get('display_name', 'General Science') if concept.get('level') == 0 else 'General Science'


def analyze_evolution_chains_with_llm(concepts: List[Dict]) -> Dict[str, List[str]]:
    """Use LLM to analyze concepts and suggest meaningful evolution chains."""
    
    if not LLM_AVAILABLE:
        return {}
    
    print("🤖 Using LLM to analyze evolution relationships...")
    
    # Group concepts by category
    concepts_by_category = {}
    for c in concepts:
        category = get_category(c)
        if category not in concepts_by_category:
            concepts_by_category[category] = []
        concepts_by_category[category].append({
            'id': c['id'].split('/')[-1],
            'name': c.get('display_name', ''),
            'level': c.get('level', 0),
            'description': (c.get('description') or '')[:200]
        })
    
    # Analyze each category with LLM
    evolution_chains = {}
    
    for category, cat_concepts in list(concepts_by_category.items())[:10]:  # Limit to top 10 categories
        if len(cat_concepts) < 3:
            continue
            
        print(f"   Analyzing {category}...")
        
        # Prepare prompt
        concept_list = "\n".join([
            f"- {c['name']} (ID: {c['id']}, Level: {c['level']}): {c['description']}"
            for c in cat_concepts[:20]  # Limit to 20 concepts per category
        ])
        
        prompt = f"""Analyze these {category} concepts and identify evolutionary relationships.
Create a chronological evolution chain showing how ideas evolved from foundational to modern.

Concepts:
{concept_list}

Return a JSON array of evolution chains. Each chain is an array of concept IDs showing progression.
Example: [["id1", "id2", "id3"], ["id4", "id5"]]

Focus on:
1. Chronological progression (earlier concepts → later concepts)
2. Conceptual dependencies (foundation → application)
3. Historical influence (what enabled what)

Return ONLY the JSON array, no explanation."""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            chains = json.loads(response_text)
            evolution_chains[category] = chains
            print(f"      ✓ Found {len(chains)} evolution chains")
            
            time.sleep(1)  # Rate limiting for Gemini
            
        except Exception as e:
            print(f"      ⚠️  LLM analysis failed: {e}")
            continue
    
    return evolution_chains


def generate_rule_based_edges(concepts: List[Dict], ideas_map: Dict[str, IdeaNode]) -> List[InfluenceEdge]:
    """Generate edges using rule-based approach (fallback when LLM unavailable)."""
    
    print("🔗 Generating edges using rule-based approach...")
    edges = []
    
    # 1. OpenAlex ancestor relationships
    for c in concepts:
        c_id = c['id'].split('/')[-1]
        if c_id not in ideas_map:
            continue
        
        ancestors = c.get('ancestors') or []
        for anc in ancestors[:3]:  # Limit to 3 ancestors
            if not anc:
                continue
            anc_id = anc['id'].split('/')[-1]
            if anc_id in ideas_map and anc_id != c_id:
                edges.append(InfluenceEdge(
                    source_id=anc_id,
                    target_id=c_id,
                    influence_type="derived_from",
                    influence_weight=0.75,
                    evidence="OpenAlex concept hierarchy",
                    confidence_score=0.85
                ))
    
    # 2. Temporal chains within categories
    ideas_by_category = {}
    for idea in ideas_map.values():
        ideas_by_category.setdefault(idea.category, []).append(idea)
    
    for category, cat_ideas in ideas_by_category.items():
        cat_ideas.sort(key=lambda x: (x.start_year, x.influence_score))
        
        # Connect sequential ideas
        for i in range(len(cat_ideas) - 1):
            prev_idea = cat_ideas[i]
            next_idea = cat_ideas[i + 1]
            
            # Check if edge already exists
            exists = any(e.source_id == prev_idea.id and e.target_id == next_idea.id for e in edges)
            if not exists:
                edges.append(InfluenceEdge(
                    source_id=prev_idea.id,
                    target_id=next_idea.id,
                    influence_type="derived_from",
                    influence_weight=0.65,
                    evidence=f"Chronological evolution in {category}",
                    confidence_score=0.75
                ))
    
    # 3. Related concepts (limited to avoid too many edges)
    for c in concepts[:50]:  # Only for top 50 concepts
        c_id = c['id'].split('/')[-1]
        if c_id not in ideas_map:
            continue
        
        related = c.get('related_concepts') or []
        for rel in related[:2]:  # Limit to 2 related
            if not rel:
                continue
            rel_id = rel['id'].split('/')[-1]
            if rel_id in ideas_map and rel_id != c_id:
                # Only add if target has higher influence (avoid bidirectional)
                if ideas_map[rel_id].influence_score > ideas_map[c_id].influence_score:
                    edges.append(InfluenceEdge(
                        source_id=c_id,
                        target_id=rel_id,
                        influence_type="inspired_by",
                        influence_weight=0.5,
                        evidence="OpenAlex related concept",
                        confidence_score=0.6
                    ))
    
    return edges


def generate_llm_based_edges(evolution_chains: Dict[str, List[List[str]]], ideas_map: Dict[str, IdeaNode]) -> List[InfluenceEdge]:
    """Generate edges based on LLM-identified evolution chains."""
    
    print("🔗 Generating edges from LLM evolution chains...")
    edges = []
    
    for category, chains in evolution_chains.items():
        for chain in chains:
            # Create edges along the chain
            for i in range(len(chain) - 1):
                source_id = chain[i]
                target_id = chain[i + 1]
                
                if source_id in ideas_map and target_id in ideas_map:
                    edges.append(InfluenceEdge(
                        source_id=source_id,
                        target_id=target_id,
                        influence_type="derived_from",
                        influence_weight=0.85,
                        evidence=f"LLM-identified evolution in {category}",
                        confidence_score=0.9
                    ))
    
    return edges


def optimize_dataset(concepts: List[Dict], max_ideas: int = 200) -> List[Dict]:
    """Optimize dataset for performance - select most impactful concepts."""
    
    print(f"\n⚡ Optimizing dataset to {max_ideas} most impactful concepts...")
    
    # Score concepts by multiple factors
    scored_concepts = []
    for c in concepts:
        score = 0
        
        # Factor 1: Works count (normalized)
        works_count = c.get('works_count', 0)
        score += min(works_count / 1000000, 1.0) * 40  # Max 40 points
        
        # Factor 2: Level diversity (prefer mix of levels)
        level = c.get('level', 0)
        level_bonus = {0: 30, 1: 25, 2: 20, 3: 15}.get(level, 10)
        score += level_bonus
        
        # Factor 3: Has ancestors (better for tree visualization)
        ancestors = c.get('ancestors') or []
        ancestors_count = len(ancestors) if ancestors else 0
        score += min(ancestors_count * 5, 20)  # Max 20 points
        
        # Factor 4: Has related concepts (better connectivity)
        related = c.get('related_concepts') or []
        related_count = len(related) if related else 0
        score += min(related_count * 2, 10)  # Max 10 points
        
        scored_concepts.append((score, c))
    
    # Sort by score and take top N
    scored_concepts.sort(reverse=True, key=lambda x: x[0])
    optimized = [c for score, c in scored_concepts[:max_ideas]]
    
    print(f"✅ Selected {len(optimized)} high-quality concepts\n")
    return optimized


def main():
    """Main execution flow."""
    
    print("=" * 70)
    print("🚀 INTELLIGENT OPENALEX DATA FETCHER WITH LLM ENHANCEMENT")
    print("=" * 70)
    
    # Configuration
    MAX_CONCEPTS = 200  # Limit for performance
    
    # Step 1: Fetch concepts from OpenAlex
    concepts = fetch_concepts(max_concepts=300)  # Fetch more, then optimize
    
    if not concepts:
        print("❌ Failed to fetch concepts. Aborting.")
        return
    
    # Step 2: Optimize dataset
    concepts = optimize_dataset(concepts, max_ideas=MAX_CONCEPTS)
    
    # Step 3: Create IdeaNodes
    print("📝 Creating idea nodes...")
    ideas_map = {}
    max_score = max((c.get('works_count', 1) for c in concepts), default=1)
    
    for idx, c in enumerate(concepts):
        c_id = c['id'].split('/')[-1]
        name = c.get('display_name', '')
        level = c.get('level', 0)
        
        stage, start_y, end_y = map_level_to_stage_and_year(level)
        category = get_category(c)
        authors = get_authors_for_concept(c_id, name)
        score = c.get('works_count', 0) / max_score
        
        idea = IdeaNode(
            id=c_id,
            title=name[:100],
            description=c.get('description') or f"Study of {name.lower()}",
            stage=stage,
            start_year=start_y,
            end_year=end_y,
            category=category,
            laureates=authors,
            motivation=f"Scholarly significance with {c.get('works_count', 0):,} works",
            keywords=[name.lower()],
            influence_score=round(max(0.1, score), 4)
        )
        
        ideas_map[c_id] = idea
        
        if (idx + 1) % 50 == 0:
            print(f"   Created {idx + 1}/{len(concepts)} ideas...")
    
    print(f"✅ Created {len(ideas_map)} idea nodes\n")
    
    # Step 4: Generate edges
    if LLM_AVAILABLE:
        # Use LLM for intelligent edge generation
        evolution_chains = analyze_evolution_chains_with_llm(concepts)
        edges = generate_llm_based_edges(evolution_chains, ideas_map)
        
        # Supplement with rule-based edges
        rule_edges = generate_rule_based_edges(concepts, ideas_map)
        
        # Combine and deduplicate
        edge_set = set()
        all_edges = []
        for edge in edges + rule_edges:
            key = (edge.source_id, edge.target_id)
            if key not in edge_set:
                edge_set.add(key)
                all_edges.append(edge)
        
        edges = all_edges
    else:
        # Use only rule-based approach
        edges = generate_rule_based_edges(concepts, ideas_map)
    
    print(f"✅ Generated {len(edges)} edges\n")
    
    # Step 5: Save to DataStore
    print("💾 Saving to DataStore...")
    data_dir = "data/evolution_tracker_api"
    
    # Backup existing data
    if os.path.exists(data_dir):
        backup_dir = f"{data_dir}_backup_{int(time.time())}"
        os.rename(data_dir, backup_dir)
        print(f"   Backed up existing data to {backup_dir}")
    
    os.makedirs(data_dir, exist_ok=True)
    store = DataStore(data_dir=data_dir)
    
    # Save ideas
    for idea in ideas_map.values():
        try:
            store.add_idea(idea)
        except ValueError:
            pass
    
    # Save edges
    for edge in edges:
        try:
            store.add_edge(edge)
        except Exception:
            pass
    
    print(f"✅ Saved {len(ideas_map)} ideas and {len(edges)} edges\n")
    
    # Step 6: Statistics
    print("=" * 70)
    print("📊 DATASET STATISTICS")
    print("=" * 70)
    print(f"Total Ideas: {len(ideas_map)}")
    print(f"Total Edges: {len(edges)}")
    print(f"Avg Edges per Idea: {len(edges) / len(ideas_map):.2f}")
    
    # Count by category
    categories = {}
    for idea in ideas_map.values():
        categories[idea.category] = categories.get(idea.category, 0) + 1
    
    print(f"\nTop Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {cat}: {count} ideas")
    
    # Count by stage
    stages = {}
    for idea in ideas_map.values():
        stages[idea.stage.value] = stages.get(idea.stage.value, 0) + 1
    
    print(f"\nEvolution Stages:")
    for stage, count in sorted(stages.items()):
        print(f"   {stage}: {count} ideas")
    
    print("\n" + "=" * 70)
    print("✅ DATASET READY!")
    print("=" * 70)
    print("\n🚀 Next steps:")
    print("   1. Restart backend: python -m backend.api")
    print("   2. Refresh frontend in browser")
    print("   3. Click on any idea to see the tree map!")
    print("\n💡 Tip: Try clicking on high-influence ideas for rich trees")
    print("=" * 70)


if __name__ == "__main__":
    main()
