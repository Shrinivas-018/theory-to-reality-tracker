"""
Dataset Exporter for the Theory-to-Reality Evolution Tracker.

Exports ideas and influence edges as structured CSV, JSON, or
graph-format datasets suitable for Kaggle-style sharing. Includes
auto-generated metadata.
"""

import csv
import json
import io
from datetime import datetime
from typing import Dict, Any, Optional

from backend.services.data_store import DataStore
from backend.services.lineage_graph import LineageGraph


class DatasetExporter:
    """Export the idea database in multiple formats with metadata."""

    def __init__(self, store: DataStore, graph: LineageGraph):
        self._store = store
        self._graph = graph

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _metadata(self) -> Dict[str, Any]:
        ideas = self._store.get_all_ideas()
        edges = self._store.get_all_edges()
        years = [i.start_year for i in ideas] if ideas else [0]
        return {
            "dataset_name": "Scientific Evolution: Theory-to-Technology Lineage",
            "description": (
                "A structured dataset tracking the evolution of human "
                "discoveries from philosophical concepts through scientific "
                "validation and engineering application to modern technology."
            ),
            "generated_at": datetime.now().isoformat(),
            "total_ideas": len(ideas),
            "total_edges": len(edges),
            "year_range": f"{min(years)}–{max(years)}",
            "columns_ideas": {
                "id": "Unique idea identifier",
                "title": "Human-readable title",
                "description": "Full-text description of the idea",
                "stage": "Evolution stage (philosophy / scientific_validation / engineering_application / modern_technology)",
                "start_year": "Year the idea was introduced",
                "end_year": "Year the idea reached its current stage",
                "category": "Domain classification (Physics, Chemistry, etc.)",
                "laureates": "Associated researchers / organisations",
                "keywords": "Descriptive keywords",
                "influence_score": "Normalised influence score [0, 1]",
            },
            "columns_edges": {
                "source_id": "ID of the influencing idea",
                "target_id": "ID of the influenced idea",
                "influence_type": "Relationship type (derived_from, applied_to, inspired_by)",
                "influence_weight": "Strength of influence [0, 1]",
                "evidence": "Textual evidence for the relationship",
                "confidence_score": "Confidence in the edge [0, 1]",
            },
            "source": "Hand-curated from historical records of scientific evolution",
        }

    # ------------------------------------------------------------------
    # CSV Export
    # ------------------------------------------------------------------

    def export_csv(self) -> Dict[str, str]:
        """
        Export as two CSV strings: one for ideas, one for edges.

        Returns dict with keys 'ideas_csv' and 'edges_csv'.
        """
        ideas = self._store.get_all_ideas()
        edges = self._store.get_all_edges()

        # Ideas CSV
        ideas_buf = io.StringIO()
        idea_fields = [
            "id", "title", "description", "stage", "start_year",
            "end_year", "category", "laureates", "keywords",
            "influence_score",
        ]
        writer = csv.DictWriter(ideas_buf, fieldnames=idea_fields)
        writer.writeheader()
        for idea in ideas:
            writer.writerow({
                "id": idea.id,
                "title": idea.title,
                "description": idea.description,
                "stage": idea.stage.value,
                "start_year": idea.start_year,
                "end_year": idea.end_year or "",
                "category": idea.category,
                "laureates": "; ".join(idea.laureates),
                "keywords": "; ".join(idea.keywords),
                "influence_score": idea.influence_score,
            })

        # Edges CSV
        edges_buf = io.StringIO()
        edge_fields = [
            "source_id", "target_id", "influence_type",
            "influence_weight", "evidence", "confidence_score",
        ]
        writer = csv.DictWriter(edges_buf, fieldnames=edge_fields)
        writer.writeheader()
        for edge in edges:
            writer.writerow({
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "influence_type": edge.influence_type,
                "influence_weight": edge.influence_weight,
                "evidence": edge.evidence,
                "confidence_score": edge.confidence_score,
            })

        return {
            "ideas_csv": ideas_buf.getvalue(),
            "edges_csv": edges_buf.getvalue(),
        }

    # ------------------------------------------------------------------
    # JSON Export
    # ------------------------------------------------------------------

    def export_json(self) -> Dict[str, Any]:
        """
        Export as a single JSON structure containing metadata, ideas,
        edges, and graph topology.
        """
        ideas = self._store.get_all_ideas()
        edges = self._store.get_all_edges()
        graph_data = self._graph.to_json()

        return {
            "metadata": self._metadata(),
            "ideas": [i.to_dict() for i in ideas],
            "edges": [e.to_dict() for e in edges],
            "graph": graph_data,
        }

    # ------------------------------------------------------------------
    # Graph Format Export
    # ------------------------------------------------------------------

    def export_graph(self) -> Dict[str, Any]:
        """
        Export a graph-only view (nodes + edges) suitable
        for network analysis tools.
        """
        return self._graph.to_json()
