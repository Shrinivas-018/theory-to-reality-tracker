"""
Yuga Data Structures Service

Uses advanced data structures for efficient querying and analysis of Yuga evolution data:
- Interval Tree: Query ideas by time period/Yuga era
- Segment Tree: Range queries for evolution complexity scores
- Lineage Graph: Track idea dependencies and evolution chains
"""

from backend.data_structures.interval_tree import IntervalTree
from backend.data_structures.segment_tree import SegmentTree
from backend.services.lineage_graph import LineageGraph
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class YugaDataStructures:
    """
    Advanced data structures for Yuga evolution analysis.
    
    WHY THESE DATA STRUCTURES:
    
    1. INTERVAL TREE:
       - Purpose: Efficiently find all ideas that existed in a specific time period
       - Use case: "Show me all ideas from Dwapar Yuga (1000 BCE - 500 CE)"
       - Time complexity: O(log n + k) where k is number of results
       - Better than: Linear scan O(n) through all ideas
    
    2. SEGMENT TREE:
       - Purpose: Range queries on evolution complexity scores
       - Use case: "Find ideas with complexity score between 50-80 in Kali Yuga"
       - Time complexity: O(log n) for range queries
       - Better than: Sorting and binary search O(n log n)
    
    3. LINEAGE GRAPH:
       - Purpose: Track how ideas evolved from each other across Yugas
       - Use case: "Show evolution chain: Fire → Cooking → Stove → Microwave"
       - Enables: Ancestor/descendant queries, influence analysis
       - Better than: Recursive database queries
    """
    
    def __init__(self):
        """Initialize data structures."""
        # Interval Tree for time-based queries
        self.time_intervals = IntervalTree()
        self.interval_count = 0  # Track number of intervals inserted
        
        # Segment Tree for complexity score queries
        self.complexity_tree = None  # Will be built when data is loaded
        
        # Lineage Graph for idea evolution chains
        self.lineage = LineageGraph()
        
        # Yuga time periods (approximate historical periods)
        self.yuga_periods = {
            "satya_yuga": (-10000, -5000),  # Ancient prehistoric times
            "treta_yuga": (-5000, -1000),   # Ancient civilizations
            "dwapar_yuga": (-1000, 1500),   # Medieval to Renaissance
            "kali_yuga": (1500, 2100)       # Modern era
        }
        
        # Loaded ideas cache
        self.ideas_cache = []
    
    def _map_year_to_range(self, year: int) -> int:
        """
        Map historical year to IntervalTree's valid range (1800-2200).
        
        Maps: -10000 to 2100 → 1800 to 2200
        """
        # Linear mapping
        old_min, old_max = -10000, 2100
        new_min, new_max = 1800, 2200
        
        # Clamp to old range
        year = max(old_min, min(old_max, year))
        
        # Map to new range
        mapped = new_min + (year - old_min) * (new_max - new_min) / (old_max - old_min)
        return int(mapped)
    
    def _unmap_year_from_range(self, mapped_year: int) -> int:
        """
        Reverse mapping from IntervalTree range back to historical year.
        """
        old_min, old_max = -10000, 2100
        new_min, new_max = 1800, 2200
        
        # Reverse the mapping
        year = old_min + (mapped_year - new_min) * (old_max - old_min) / (new_max - new_min)
        return int(year)
    
    def calculate_complexity_score(self, idea: Dict, yuga: str) -> int:
        """
        Calculate complexity score for an idea in a specific Yuga.
        
        Score based on:
        - Technology level (0-100)
        - Energy requirements (0-100)
        - Knowledge needed (0-100)
        
        Returns: Score from 0-100
        """
        evolution = idea.get("evolution", {}).get(yuga, {})
        
        # Parse statistics to estimate complexity
        stats = evolution.get("statistics", "").lower()
        
        score = 0
        
        # Energy complexity
        if "electricity" in stats or "fossil" in stats:
            score += 40
        elif "mechanical" in stats or "steam" in stats:
            score += 25
        elif "manual" in stats or "physical" in stats:
            score += 10
        else:
            score += 5  # Divine/natural
        
        # Technology level
        if "automated" in stats or "digital" in stats:
            score += 30
        elif "mechanical" in stats or "industrial" in stats:
            score += 20
        elif "crafted" in stats or "artisan" in stats:
            score += 10
        else:
            score += 5
        
        # Knowledge requirements
        characteristics = evolution.get("characteristics", "").lower()
        if "technology" in characteristics or "scientific" in characteristics:
            score += 30
        elif "skill" in characteristics or "training" in characteristics:
            score += 15
        else:
            score += 5
        
        return min(score, 100)
    
    def load_ideas(self, ideas: List[Dict]):
        """
        Load ideas into data structures.
        
        Args:
            ideas: List of idea documents from MongoDB
        """
        self.ideas_cache = ideas
        
        print(f"\n[INFO] Building data structures for {len(ideas)} ideas...")
        
        # 1. Build Interval Tree (time-based indexing)
        print("  [INFO] Building Interval Tree for time-based queries...")
        for idea in ideas:
            idea_name = idea.get("idea", "")
            
            # Add intervals for each Yuga the idea exists in
            for yuga, (start, end) in self.yuga_periods.items():
                if yuga in idea.get("evolution", {}):
                    # Map to valid year range (1800-2200) for IntervalTree
                    # We'll use a mapping: -10000 to 2100 → 1800 to 2200
                    mapped_start = self._map_year_to_range(start)
                    mapped_end = self._map_year_to_range(end)
                    
                    # Store idea name and yuga as data
                    try:
                        self.time_intervals.insert(mapped_start, mapped_end, f"{idea_name}|{yuga}")
                        self.interval_count += 1
                    except ValueError:
                        # Skip if year mapping fails
                        pass
        
        print(f"    [OK] Indexed {self.interval_count} time intervals")
        
        # 2. Build Segment Tree (complexity score indexing)
        print("  [INFO] Building Segment Tree for complexity queries...")
        
        # Calculate complexity scores for all ideas in Kali Yuga.
        # SegmentTree is indexed over the score domain 0-100.
        # Each idea's score is registered as an active "year" in the tree,
        # so range_query(min, max) returns how many ideas fall in that band,
        # and we keep complexity_mapping for retrieving the actual idea objects.
        complexity_scores = []
        for idea in ideas:
            score = self.calculate_complexity_score(idea, "kali_yuga")
            complexity_scores.append((score, idea.get("idea", "")))
        
        if complexity_scores:
            # Build tree over score domain 0-100
            self.complexity_tree = SegmentTree(min_year=0, max_year=100)
            for score, _ in complexity_scores:
                self.complexity_tree.update(score, score, 1)
            self.complexity_mapping = complexity_scores
        
        print(f"    [OK] Built segment tree with {len(complexity_scores)} scores")
        
        # 3. Build Lineage Graph (idea evolution chains)
        print("  [INFO] Building Lineage Graph for evolution chains...")
        
        # Define evolution chains (parent → child relationships)
        evolution_chains = self._detect_evolution_chains(ideas)
        
        # First add all nodes
        for idea in ideas:
            idea_name = idea.get("idea", "")
            try:
                self.lineage.add_idea_simple(
                    idea_id=idea_name,
                    title=idea_name,
                    stage="kali_yuga",
                    start_year=2000
                )
            except ValueError:
                # Already exists
                pass
        
        # Then add edges
        for parent, child in evolution_chains:
            try:
                self.lineage.add_influence_simple(
                    source_id=parent,
                    target_id=child,
                    influence_type="evolved_into",
                    weight=1.0
                )
            except ValueError:
                # Node doesn't exist
                pass
        
        print(f"    [OK] Created {len(evolution_chains)} evolution relationships")
        print("[OK] Data structures built successfully!\n")
    
    def _detect_evolution_chains(self, ideas: List[Dict]) -> List[Tuple[str, str]]:
        """
        Detect evolution chains between ideas based on their descriptions.
        
        Returns: List of (parent, child) tuples
        """
        import json
        chains = []
        
        # Manual evolution chains (domain knowledge)
        known_chains = [
            # Cooking evolution
            ("Fire", "Cooking"),
            ("Cooking", "Pressure Cooker"),
            ("Pressure Cooker", "Microwave Oven"),
            
            # Transportation evolution
            ("Wheel", "Bicycle"),
            ("Bicycle", "Motorcycle"),
            ("Motorcycle", "Automobile"),
            ("Automobile", "Electric Cars"),
            
            # Communication evolution
            ("Paper", "Printing Press"),
            ("Printing Press", "Typewriter"),
            ("Telegraph", "Telephone"),
            ("Telephone", "Radio"),
            ("Radio", "Television"),
            
            # Energy evolution
            ("Fire", "Heating System"),
            ("Electricity", "Light Bulb"),
            ("Light Bulb", "LED Lighting"),
            
            # Medicine evolution
            ("Microscope", "Vaccines"),
            ("X-Ray", "MRI"),
            ("MRI", "CT Scan"),
            
            # Science evolution
            ("Gravity", "Relativity"),
            ("Atomic Theory", "Quantum Mechanics"),
            ("Electricity", "Magnetism"),
            
            # Tools evolution
            ("Hammer", "Drill"),
            ("Saw", "Power Tools"),
        ]
        
        # 1. Map lower-case names to original names for robust matching
        idea_names_lower = {idea.get("idea", "").lower(): idea.get("idea", "") for idea in ideas if idea.get("idea")}
        
        for parent, child in known_chains:
            p_lower, c_lower = parent.lower(), child.lower()
            if p_lower in idea_names_lower and c_lower in idea_names_lower:
                chains.append((idea_names_lower[p_lower], idea_names_lower[c_lower]))
                
        # 2. Dynamic detection: if Idea A's name is in Idea B's text, it's an influence
        for idea_b in ideas:
            b_name = idea_b.get("idea", "")
            if not b_name:
                continue
                
            # Combine all text of B to search for A's name
            b_text = str(idea_b.get("description", "")).lower()
            b_evo = idea_b.get("evolution", {})
            for yuga_data in b_evo.values():
                if isinstance(yuga_data, dict):
                    b_text += " " + str(yuga_data.get("description", "")).lower()
            
            for idea_a in ideas:
                a_name = idea_a.get("idea", "")
                if not a_name or a_name.lower() == b_name.lower() or len(a_name) < 4:
                    continue
                
                a_lower = a_name.lower()
                # If A is explicitly mentioned in B's text
                if a_lower in b_text:
                    edge = (a_name, b_name)
                    reverse_edge = (b_name, a_name)
                    if edge not in chains and reverse_edge not in chains:
                        chains.append(edge)
        
        return chains
    
    def query_by_time_period(self, start_year: int, end_year: int) -> List[Dict]:
        """
        Query ideas that existed in a specific time period using Interval Tree.
        
        Args:
            start_year: Start year (e.g., -1000 for 1000 BCE)
            end_year: End year (e.g., 1500 for 1500 CE)
        
        Returns: List of ideas with their Yuga data
        
        Time Complexity: O(log n + k) where k is number of results
        """
        # Map years to IntervalTree range
        mapped_start = self._map_year_to_range(start_year)
        mapped_end = self._map_year_to_range(end_year)
        
        try:
            result_ids = self.time_intervals.query(mapped_start, mapped_end)
        except ValueError:
            return []
        
        # Parse results and deduplicate by idea name
        unique_ideas = {}
        for result_id in result_ids:
            # result_id format: "idea_name|yuga"
            parts = result_id.split("|")
            if len(parts) == 2:
                idea_name, yuga = parts
                if idea_name not in unique_ideas:
                    # Find the full idea data
                    for idea in self.ideas_cache:
                        if idea.get("idea", "") == idea_name:
                            unique_ideas[idea_name] = idea
                            break
        
        return list(unique_ideas.values())
    
    def query_by_complexity_range(self, min_score: int, max_score: int, yuga: str = "kali_yuga") -> List[Dict]:
        """
        Query ideas by complexity score range using Segment Tree.
        
        The Segment Tree is indexed over the score domain 0-100.
        range_query(min, max) confirms how many ideas fall in the band (O(log n)),
        then we retrieve the matching idea objects from complexity_mapping.
        
        Args:
            min_score: Minimum complexity score (0-100)
            max_score: Maximum complexity score (0-100)
            yuga: Which Yuga to analyze
        
        Returns: List of ideas in the complexity range
        
        Time Complexity: O(log n) for the range check + O(k) to collect k results
        """
        if not self.complexity_tree or not self.complexity_mapping:
            return []
        
        # Clamp to valid domain
        min_score = max(0, min_score)
        max_score = min(100, max_score)
        
        # Use Segment Tree to verify count in range (O(log n))
        count_in_range = self.complexity_tree.range_query(min_score, max_score)
        
        if count_in_range == 0:
            return []
        
        # Collect the actual idea objects whose scores fall in range
        # Build a fast lookup: idea_name → full idea doc
        idea_lookup = {idea.get("idea", ""): idea for idea in self.ideas_cache}
        
        results = []
        for score, idea_name in self.complexity_mapping:
            if min_score <= score <= max_score:
                idea = idea_lookup.get(idea_name)
                if idea:
                    results.append({
                        "idea": idea,
                        "complexity_score": score
                    })
        
        return results
    
    def get_evolution_chain(self, idea_name: str) -> Dict:
        """
        Get the evolution chain for an idea using Lineage Graph.
        
        Args:
            idea_name: Name of the idea
        
        Returns: Dict with ancestors and descendants
        """
        if idea_name not in self.lineage._graph:
            return {
                "ancestors": [],
                "descendants": [],
                "chain_length": 0
            }
        
        # Get ancestors (what this idea evolved from)
        ancestors = self.lineage.get_ancestors(idea_name)
        
        # Get descendants (what evolved from this idea)
        descendants = self.lineage.get_descendants(idea_name)
        
        return {
            "ancestors": ancestors,
            "descendants": descendants,
            "chain_length": len(ancestors) + len(descendants) + 1
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about the data structures."""
        return {
            "total_ideas": len(self.ideas_cache),
            "interval_tree_size": self.interval_count,
            "segment_tree_built": self.complexity_tree is not None,
            "lineage_graph_nodes": self.lineage.node_count,
            "lineage_graph_edges": self.lineage.edge_count,
            "yuga_periods": self.yuga_periods
        }
