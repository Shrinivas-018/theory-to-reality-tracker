"""
Tests for the Dataset Exporter.

Covers CSV export, JSON export, graph export, and metadata generation.
"""

import json
import pytest
from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services.data_store import DataStore
from backend.services.lineage_graph import LineageGraph
from backend.services.dataset_exporter import DatasetExporter


# ─── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def temp_store(tmp_path):
    return DataStore(data_dir=str(tmp_path / "test_export"))


@pytest.fixture
def graph():
    return LineageGraph()


def _idea(id, title, stage, year, **kw):
    return IdeaNode(
        id=id, title=title,
        description=f"Desc for {title}",
        stage=stage, start_year=year,
        category=kw.get("category", "Physics"),
        laureates=["Tester"],
        motivation="Motivation",
        keywords=kw.get("keywords", ["keyword"]),
        influence_score=kw.get("influence_score", 0.5),
    )


@pytest.fixture
def seeded(temp_store, graph):
    ideas = [
        _idea("a", "Idea A", EvolutionStage.PHILOSOPHY, 1800),
        _idea("b", "Idea B", EvolutionStage.MODERN_TECHNOLOGY, 2020),
    ]
    for i in ideas:
        temp_store.add_idea(i)
        graph.add_idea(i)
    edge = InfluenceEdge(
        source_id="a", target_id="b",
        influence_type="derived_from", influence_weight=0.9,
        evidence="Test evidence", confidence_score=0.85,
    )
    temp_store.add_edge(edge)
    graph.add_influence(edge)
    return temp_store, graph


@pytest.fixture
def exporter(seeded):
    store, g = seeded
    return DatasetExporter(store, g)


# ─── CSV Export ──────────────────────────────────────────────────

class TestCSVExport:
    def test_csv_has_both_keys(self, exporter):
        result = exporter.export_csv()
        assert "ideas_csv" in result
        assert "edges_csv" in result

    def test_csv_ideas_header(self, exporter):
        csv = exporter.export_csv()["ideas_csv"]
        header = csv.split("\n")[0]
        assert "id" in header
        assert "title" in header
        assert "stage" in header

    def test_csv_edges_header(self, exporter):
        csv = exporter.export_csv()["edges_csv"]
        header = csv.split("\n")[0]
        assert "source_id" in header
        assert "target_id" in header

    def test_csv_idea_rows(self, exporter):
        csv = exporter.export_csv()["ideas_csv"]
        lines = [l for l in csv.strip().split("\n") if l]
        assert len(lines) == 3  # header + 2 ideas

    def test_csv_edge_rows(self, exporter):
        csv = exporter.export_csv()["edges_csv"]
        lines = [l for l in csv.strip().split("\n") if l]
        assert len(lines) == 2  # header + 1 edge


# ─── JSON Export ─────────────────────────────────────────────────

class TestJSONExport:
    def test_json_has_metadata(self, exporter):
        data = exporter.export_json()
        assert "metadata" in data
        assert "dataset_name" in data["metadata"]
        assert "generated_at" in data["metadata"]

    def test_json_has_ideas(self, exporter):
        data = exporter.export_json()
        assert "ideas" in data
        assert len(data["ideas"]) == 2

    def test_json_has_edges(self, exporter):
        data = exporter.export_json()
        assert "edges" in data
        assert len(data["edges"]) == 1

    def test_json_has_graph(self, exporter):
        data = exporter.export_json()
        assert "graph" in data
        assert "nodes" in data["graph"]
        assert "edges" in data["graph"]

    def test_json_metadata_counts(self, exporter):
        data = exporter.export_json()
        assert data["metadata"]["total_ideas"] == 2
        assert data["metadata"]["total_edges"] == 1


# ─── Graph Export ────────────────────────────────────────────────

class TestGraphExport:
    def test_graph_has_nodes_and_edges(self, exporter):
        data = exporter.export_graph()
        assert "nodes" in data
        assert "edges" in data

    def test_graph_node_count(self, exporter):
        data = exporter.export_graph()
        assert len(data["nodes"]) == 2

    def test_graph_edge_count(self, exporter):
        data = exporter.export_graph()
        assert len(data["edges"]) == 1


# ─── Empty Dataset ───────────────────────────────────────────────

class TestEmptyExport:
    def test_empty_csv(self, temp_store, graph):
        empty_store = DataStore(data_dir=str(temp_store.data_dir) + "_empty")
        ex = DatasetExporter(empty_store, graph)
        result = ex.export_csv()
        ideas_lines = [l for l in result["ideas_csv"].strip().split("\n") if l]
        assert len(ideas_lines) == 1  # only header

    def test_empty_json(self, temp_store, graph):
        empty_store = DataStore(data_dir=str(temp_store.data_dir) + "_empty2")
        ex = DatasetExporter(empty_store, LineageGraph())
        data = ex.export_json()
        assert data["metadata"]["total_ideas"] == 0
        assert len(data["ideas"]) == 0
