"""
Lineage Graph Manager for tracking idea evolution relationships.

Uses NetworkX DiGraph to model how ideas influence and evolve from
one another. Supports ancestor/descendant queries, path finding,
centrality measures, and cycle detection.
"""

import networkx as nx
from typing import List, Dict, Optional, Any, Tuple

from backend.models import IdeaNode, InfluenceEdge


class LineageGraph:
    """
    Directed graph representing idea evolution lineage.

    Nodes represent ideas, edges represent influence relationships.
    Provides graph traversal, path finding, and centrality analysis.
    """

    def __init__(self):
        """Initialize an empty lineage graph."""
        self._graph = nx.DiGraph()

    @property
    def node_count(self) -> int:
        """Number of ideas in the graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Number of influence relationships in the graph."""
        return self._graph.number_of_edges()

    # --- Node operations ---

    def add_idea(self, idea: IdeaNode) -> None:
        """
        Add an idea as a node in the graph.

        Args:
            idea: IdeaNode to add

        Raises:
            ValueError: If idea already exists in graph
        """
        if idea.id in self._graph:
            raise ValueError(f"Idea '{idea.id}' already exists in graph")

        self._graph.add_node(
            idea.id,
            title=idea.title,
            description=idea.description,
            stage=idea.stage.value,
            start_year=idea.start_year,
            end_year=idea.end_year,
            category=idea.category,
            influence_score=idea.influence_score,
            keywords=idea.keywords,
        )

    def add_idea_simple(
        self,
        idea_id: str,
        title: str = "",
        stage: str = "",
        start_year: int = 0,
        **kwargs
    ) -> None:
        """
        Add an idea using simple attributes (no IdeaNode required).

        Args:
            idea_id: Unique identifier
            title: Idea title
            stage: Evolution stage string
            start_year: Start year
            **kwargs: Additional attributes
        """
        if idea_id in self._graph:
            raise ValueError(f"Idea '{idea_id}' already exists in graph")

        self._graph.add_node(
            idea_id,
            title=title,
            stage=stage,
            start_year=start_year,
            **kwargs,
        )

    def remove_idea(self, idea_id: str) -> None:
        """
        Remove an idea and all its edges from the graph.

        Args:
            idea_id: ID of the idea to remove

        Raises:
            ValueError: If idea not found
        """
        if idea_id not in self._graph:
            raise ValueError(f"Idea '{idea_id}' not found in graph")
        self._graph.remove_node(idea_id)

    def has_idea(self, idea_id: str) -> bool:
        """Check if an idea exists in the graph."""
        return idea_id in self._graph

    def get_idea_attrs(self, idea_id: str) -> Dict[str, Any]:
        """
        Get all attributes of an idea node.

        Args:
            idea_id: ID of the idea

        Returns:
            Dictionary of node attributes

        Raises:
            ValueError: If idea not found
        """
        if idea_id not in self._graph:
            raise ValueError(f"Idea '{idea_id}' not found in graph")
        return dict(self._graph.nodes[idea_id])

    # --- Edge operations ---

    def add_influence(self, edge: InfluenceEdge) -> None:
        """
        Add a directed influence edge between ideas.

        Args:
            edge: InfluenceEdge to add

        Raises:
            ValueError: If source or target not in graph
        """
        if edge.source_id not in self._graph:
            raise ValueError(f"Source idea '{edge.source_id}' not found")
        if edge.target_id not in self._graph:
            raise ValueError(f"Target idea '{edge.target_id}' not found")

        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            influence_type=edge.influence_type,
            influence_weight=edge.influence_weight,
            evidence=edge.evidence,
            confidence_score=edge.confidence_score,
        )

    def add_influence_simple(
        self,
        source_id: str,
        target_id: str,
        influence_type: str = "derived_from",
        weight: float = 0.5,
    ) -> None:
        """
        Add a directed influence edge using simple attributes.

        Args:
            source_id: ID of the influencing idea
            target_id: ID of the influenced idea
            influence_type: Type of influence
            weight: Influence weight

        Raises:
            ValueError: If source or target not in graph
        """
        if source_id not in self._graph:
            raise ValueError(f"Source idea '{source_id}' not found")
        if target_id not in self._graph:
            raise ValueError(f"Target idea '{target_id}' not found")

        self._graph.add_edge(
            source_id,
            target_id,
            influence_type=influence_type,
            influence_weight=weight,
        )

    def remove_influence(self, source_id: str, target_id: str) -> None:
        """
        Remove an influence edge.

        Args:
            source_id: Source idea ID
            target_id: Target idea ID

        Raises:
            ValueError: If edge not found
        """
        if not self._graph.has_edge(source_id, target_id):
            raise ValueError(
                f"No edge from '{source_id}' to '{target_id}'"
            )
        self._graph.remove_edge(source_id, target_id)

    # --- Ancestor / Descendant queries ---

    def get_ancestors(self, idea_id: str) -> List[str]:
        """
        Get all ancestor ideas (direct and transitive predecessors).

        Args:
            idea_id: ID of the idea

        Returns:
            List of ancestor idea IDs

        Raises:
            ValueError: If idea not found
        """
        if idea_id not in self._graph:
            raise ValueError(f"Idea '{idea_id}' not found")
        return list(nx.ancestors(self._graph, idea_id))

    def get_descendants(self, idea_id: str) -> List[str]:
        """
        Get all descendant ideas (direct and transitive successors).

        Args:
            idea_id: ID of the idea

        Returns:
            List of descendant idea IDs

        Raises:
            ValueError: If idea not found
        """
        if idea_id not in self._graph:
            raise ValueError(f"Idea '{idea_id}' not found")
        return list(nx.descendants(self._graph, idea_id))

    def get_direct_influences(self, idea_id: str) -> List[str]:
        """Get ideas directly influenced by this idea."""
        if idea_id not in self._graph:
            raise ValueError(f"Idea '{idea_id}' not found")
        return list(self._graph.successors(idea_id))

    def get_influenced_by(self, idea_id: str) -> List[str]:
        """Get ideas that directly influence this idea."""
        if idea_id not in self._graph:
            raise ValueError(f"Idea '{idea_id}' not found")
        return list(self._graph.predecessors(idea_id))

    # --- Path finding ---

    def find_evolution_path(
        self, source_id: str, target_id: str
    ) -> Optional[List[str]]:
        """
        Find the shortest evolution path between two ideas.

        Args:
            source_id: Starting idea
            target_id: Ending idea

        Returns:
            List of idea IDs forming the path, or None if no path exists

        Raises:
            ValueError: If source or target not found
        """
        if source_id not in self._graph:
            raise ValueError(f"Source idea '{source_id}' not found")
        if target_id not in self._graph:
            raise ValueError(f"Target idea '{target_id}' not found")

        try:
            return list(nx.shortest_path(
                self._graph, source_id, target_id
            ))
        except nx.NetworkXNoPath:
            return None

    def find_all_paths(
        self, source_id: str, target_id: str
    ) -> List[List[str]]:
        """
        Find all simple paths between two ideas.

        Args:
            source_id: Starting idea
            target_id: Ending idea

        Returns:
            List of paths (each a list of idea IDs)
        """
        if source_id not in self._graph:
            raise ValueError(f"Source idea '{source_id}' not found")
        if target_id not in self._graph:
            raise ValueError(f"Target idea '{target_id}' not found")

        return list(nx.all_simple_paths(
            self._graph, source_id, target_id
        ))

    # --- Centrality / Analysis ---

    def get_influence_centrality(self) -> Dict[str, float]:
        """
        Calculate PageRank-style influence centrality for all ideas.

        Returns:
            Dictionary mapping idea IDs to centrality scores (0.0–1.0)
        """
        if self._graph.number_of_nodes() == 0:
            return {}

        try:
            scores = nx.pagerank(self._graph, alpha=0.85)
        except nx.PowerIterationFailedConvergence:
            # Fall back to uniform scores
            n = self._graph.number_of_nodes()
            scores = {node: 1.0 / n for node in self._graph}

        # Normalize to [0, 1]
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in the lineage graph.

        A well-formed lineage should be a DAG (no cycles).

        Returns:
            List of cycles (each a list of idea IDs), empty if DAG
        """
        try:
            return list(nx.simple_cycles(self._graph))
        except nx.NetworkXError:
            return []

    def is_dag(self) -> bool:
        """Check if the lineage graph is a directed acyclic graph."""
        return nx.is_directed_acyclic_graph(self._graph)

    # --- Serialization ---

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize the graph to a JSON-compatible dictionary.

        Returns:
            Dictionary with 'nodes' and 'edges' lists
        """
        nodes = []
        for node_id, attrs in self._graph.nodes(data=True):
            nodes.append({"id": node_id, **attrs})

        edges = []
        for source, target, attrs in self._graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                **attrs,
            })

        return {"nodes": nodes, "edges": edges}

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'LineageGraph':
        """
        Deserialize a graph from a JSON dictionary.

        Args:
            data: Dictionary with 'nodes' and 'edges' keys

        Returns:
            LineageGraph instance
        """
        graph = cls()

        for node in data.get("nodes", []):
            node_id = node.pop("id")
            graph._graph.add_node(node_id, **node)

        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            graph._graph.add_edge(source, target, **edge)

        return graph

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the lineage graph.

        Returns:
            Dictionary with graph metrics
        """
        stats = {
            "total_nodes": self.node_count,
            "total_edges": self.edge_count,
            "is_dag": self.is_dag(),
        }

        if self.node_count > 0:
            in_degrees = dict(self._graph.in_degree())
            out_degrees = dict(self._graph.out_degree())

            # Root ideas (no predecessors)
            stats["root_ideas"] = [
                n for n, d in in_degrees.items() if d == 0
            ]
            # Leaf ideas (no successors)
            stats["leaf_ideas"] = [
                n for n, d in out_degrees.items() if d == 0
            ]
            stats["avg_in_degree"] = (
                sum(in_degrees.values()) / len(in_degrees)
            )
            stats["avg_out_degree"] = (
                sum(out_degrees.values()) / len(out_degrees)
            )

        return stats
