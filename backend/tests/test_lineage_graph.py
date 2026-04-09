"""
Tests for the Lineage Graph Manager.

Tests cover:
- Node (idea) operations: add, remove, has, attributes
- Edge (influence) operations: add, remove
- Ancestor and descendant queries
- Path finding (shortest and all paths)
- Centrality measures (PageRank)
- Cycle detection and DAG verification
- Serialization to/from JSON
- Graph statistics
"""

import pytest
from backend.services.lineage_graph import LineageGraph
from backend.models import IdeaNode, InfluenceEdge, EvolutionStage


# --- Helpers ---

def _make_graph_with_chain():
    """Create a graph with a linear chain: A -> B -> C -> D."""
    g = LineageGraph()
    for name in ["A", "B", "C", "D"]:
        g.add_idea_simple(name, title=f"Idea {name}")
    g.add_influence_simple("A", "B")
    g.add_influence_simple("B", "C")
    g.add_influence_simple("C", "D")
    return g


class TestLineageGraphNodeOps:
    """Tests for node operations."""

    def test_add_idea_simple(self):
        g = LineageGraph()
        g.add_idea_simple("idea_1", title="First Idea")
        assert g.has_idea("idea_1")
        assert g.node_count == 1

    def test_add_duplicate_raises(self):
        g = LineageGraph()
        g.add_idea_simple("idea_1")
        with pytest.raises(ValueError, match="already exists"):
            g.add_idea_simple("idea_1")

    def test_remove_idea(self):
        g = LineageGraph()
        g.add_idea_simple("idea_1")
        g.remove_idea("idea_1")
        assert not g.has_idea("idea_1")
        assert g.node_count == 0

    def test_remove_missing_raises(self):
        g = LineageGraph()
        with pytest.raises(ValueError, match="not found"):
            g.remove_idea("nope")

    def test_get_idea_attrs(self):
        g = LineageGraph()
        g.add_idea_simple("a", title="Alpha", stage="philosophy", start_year=1900)
        attrs = g.get_idea_attrs("a")
        assert attrs["title"] == "Alpha"
        assert attrs["stage"] == "philosophy"

    def test_add_idea_from_model(self):
        g = LineageGraph()
        idea = IdeaNode(
            id="qm_1925", title="Quantum Mechanics",
            description="Foundation", stage=EvolutionStage.PHILOSOPHY,
            start_year=1925, category="Physics",
            laureates=["Heisenberg"], motivation="Fun",
            keywords=["quantum"], influence_score=0.9
        )
        g.add_idea(idea)
        assert g.has_idea("qm_1925")
        assert g.get_idea_attrs("qm_1925")["stage"] == "philosophy"


class TestLineageGraphEdgeOps:
    """Tests for edge operations."""

    def test_add_influence_simple(self):
        g = LineageGraph()
        g.add_idea_simple("a")
        g.add_idea_simple("b")
        g.add_influence_simple("a", "b")
        assert g.edge_count == 1

    def test_add_influence_missing_source(self):
        g = LineageGraph()
        g.add_idea_simple("b")
        with pytest.raises(ValueError, match="Source"):
            g.add_influence_simple("a", "b")

    def test_remove_influence(self):
        g = LineageGraph()
        g.add_idea_simple("a")
        g.add_idea_simple("b")
        g.add_influence_simple("a", "b")
        g.remove_influence("a", "b")
        assert g.edge_count == 0

    def test_remove_missing_edge_raises(self):
        g = LineageGraph()
        g.add_idea_simple("a")
        g.add_idea_simple("b")
        with pytest.raises(ValueError, match="No edge"):
            g.remove_influence("a", "b")


class TestLineageGraphTraversal:
    """Tests for ancestor/descendant queries."""

    def test_get_ancestors(self):
        g = _make_graph_with_chain()
        ancestors = g.get_ancestors("D")
        assert set(ancestors) == {"A", "B", "C"}

    def test_get_descendants(self):
        g = _make_graph_with_chain()
        desc = g.get_descendants("A")
        assert set(desc) == {"B", "C", "D"}

    def test_ancestors_of_root_is_empty(self):
        g = _make_graph_with_chain()
        assert g.get_ancestors("A") == []

    def test_descendants_of_leaf_is_empty(self):
        g = _make_graph_with_chain()
        assert g.get_descendants("D") == []

    def test_direct_influences(self):
        g = _make_graph_with_chain()
        assert g.get_direct_influences("B") == ["C"]

    def test_influenced_by(self):
        g = _make_graph_with_chain()
        assert g.get_influenced_by("C") == ["B"]


class TestLineageGraphPathFinding:
    """Tests for path finding."""

    def test_shortest_path(self):
        g = _make_graph_with_chain()
        path = g.find_evolution_path("A", "D")
        assert path == ["A", "B", "C", "D"]

    def test_no_path_returns_none(self):
        g = _make_graph_with_chain()
        assert g.find_evolution_path("D", "A") is None

    def test_find_all_paths(self):
        g = LineageGraph()
        for n in ["A", "B", "C", "D"]:
            g.add_idea_simple(n)
        g.add_influence_simple("A", "B")
        g.add_influence_simple("A", "C")
        g.add_influence_simple("B", "D")
        g.add_influence_simple("C", "D")
        paths = g.find_all_paths("A", "D")
        assert len(paths) == 2

    def test_path_missing_node_raises(self):
        g = _make_graph_with_chain()
        with pytest.raises(ValueError, match="not found"):
            g.find_evolution_path("X", "A")


class TestLineageGraphAnalysis:
    """Tests for centrality, cycles, and DAG checks."""

    def test_influence_centrality(self):
        g = _make_graph_with_chain()
        scores = g.get_influence_centrality()
        assert len(scores) == 4
        # D should have highest centrality (most influenced)
        assert scores["D"] > 0

    def test_centrality_empty_graph(self):
        g = LineageGraph()
        assert g.get_influence_centrality() == {}

    def test_is_dag_true(self):
        g = _make_graph_with_chain()
        assert g.is_dag()

    def test_detect_cycles_none_in_dag(self):
        g = _make_graph_with_chain()
        assert g.detect_cycles() == []

    def test_detect_cycle(self):
        g = LineageGraph()
        for n in ["A", "B", "C"]:
            g.add_idea_simple(n)
        g.add_influence_simple("A", "B")
        g.add_influence_simple("B", "C")
        g.add_influence_simple("C", "A")  # Creates a cycle
        assert not g.is_dag()
        assert len(g.detect_cycles()) > 0


class TestLineageGraphSerialization:
    """Tests for JSON serialization."""

    def test_to_json(self):
        g = _make_graph_with_chain()
        data = g.to_json()
        assert len(data["nodes"]) == 4
        assert len(data["edges"]) == 3

    def test_roundtrip(self):
        g = _make_graph_with_chain()
        data = g.to_json()
        g2 = LineageGraph.from_json(data)
        assert g2.node_count == 4
        assert g2.edge_count == 3
        assert g2.find_evolution_path("A", "D") == ["A", "B", "C", "D"]


class TestLineageGraphStats:
    """Tests for graph statistics."""

    def test_stats(self):
        g = _make_graph_with_chain()
        stats = g.get_stats()
        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 3
        assert stats["is_dag"] is True
        assert "A" in stats["root_ideas"]
        assert "D" in stats["leaf_ideas"]
