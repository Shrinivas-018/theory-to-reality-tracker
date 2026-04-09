"""
Tests for the AI Prediction Service.

Covers TF-IDF similarity, multi-feature dormant idea detection,
evolution forecasting with confidence and explainability, and
the combined prediction overview.
"""

import pytest
from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services.data_store import DataStore
from backend.services.lineage_graph import LineageGraph
from backend.services.ai_prediction import AIPredictionService


# ─── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def temp_store(tmp_path):
    """Create a DataStore backed by a temporary directory."""
    return DataStore(data_dir=str(tmp_path / "test_data"))


@pytest.fixture
def sample_graph():
    return LineageGraph()


def _make_idea(
    id, title, stage, start_year, end_year=None,
    category="Physics", keywords=None, influence_score=0.5,
):
    return IdeaNode(
        id=id, title=title,
        description=f"Description of {title}",
        stage=stage,
        start_year=start_year,
        end_year=end_year,
        category=category,
        laureates=["Test Person"],
        motivation="Test motivation",
        keywords=keywords or ["test"],
        influence_score=influence_score,
    )


@pytest.fixture
def seeded_store(temp_store, sample_graph):
    """Store + graph pre-loaded with a mini evolution chain."""
    ideas = [
        _make_idea("philo_1800", "Ancient Theory", EvolutionStage.PHILOSOPHY,
                    1800, 1850, keywords=["theory", "classical", "philosophy"]),
        _make_idea("sci_1900", "Validation Experiment", EvolutionStage.SCIENTIFIC_VALIDATION,
                    1900, 1920, keywords=["experiment", "validation", "science"]),
        _make_idea("eng_1950", "Applied Mechanism", EvolutionStage.ENGINEERING_APPLICATION,
                    1950, 1980, keywords=["engineering", "mechanism", "applied"]),
        _make_idea("tech_2020", "Modern Product", EvolutionStage.MODERN_TECHNOLOGY,
                    2020, 2025, keywords=["technology", "product", "modern"],
                    influence_score=0.9),
    ]
    edges = [
        ("philo_1800", "sci_1900", "derived_from", 0.9),
        ("sci_1900", "eng_1950", "applied_to", 0.8),
        ("eng_1950", "tech_2020", "applied_to", 0.85),
    ]
    for idea in ideas:
        temp_store.add_idea(idea)
        sample_graph.add_idea(idea)
    for src, tgt, itype, w in edges:
        edge = InfluenceEdge(
            source_id=src, target_id=tgt,
            influence_type=itype, influence_weight=w,
            evidence="Test", confidence_score=0.9,
        )
        temp_store.add_edge(edge)
        sample_graph.add_influence(edge)

    return temp_store, sample_graph


@pytest.fixture
def prediction_svc(seeded_store):
    store, graph = seeded_store
    return AIPredictionService(store, graph)


# ─── TF-IDF Similarity ──────────────────────────────────────────

class TestTFIDFSimilarity:
    def test_similar_ideas_returns_list(self, prediction_svc):
        results = prediction_svc.get_similar_ideas("philo_1800", top_n=3)
        assert isinstance(results, list)
        assert len(results) <= 3

    def test_similar_ideas_excludes_self(self, prediction_svc):
        results = prediction_svc.get_similar_ideas("philo_1800")
        ids = [r["id"] for r in results]
        assert "philo_1800" not in ids

    def test_similar_ideas_has_required_fields(self, prediction_svc):
        results = prediction_svc.get_similar_ideas("philo_1800", top_n=1)
        if results:
            r = results[0]
            assert "id" in r
            assert "title" in r
            assert "similarity" in r
            assert "common_keywords" in r

    def test_similar_ideas_invalid_id(self, prediction_svc):
        with pytest.raises(ValueError, match="not found"):
            prediction_svc.get_similar_ideas("nonexistent_id")

    def test_similar_ideas_single_idea(self, temp_store, sample_graph):
        """With only one idea, should return empty list."""
        single_store = DataStore(data_dir=str(temp_store.data_dir) + "_single")
        sg = LineageGraph()
        idea = _make_idea("only_one", "Solo", EvolutionStage.PHILOSOPHY, 1900)
        single_store.add_idea(idea)
        sg.add_idea(idea)
        svc = AIPredictionService(single_store, sg)
        assert svc.get_similar_ideas("only_one") == []

    def test_similarity_scores_are_sorted(self, prediction_svc):
        results = prediction_svc.get_similar_ideas("philo_1800")
        scores = [r["similarity"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ─── Dormant Idea Detection ─────────────────────────────────────

class TestDormantDetection:
    def test_dormant_ideas_returns_list(self, prediction_svc):
        dormant = prediction_svc.get_dormant_ideas()
        assert isinstance(dormant, list)

    def test_dormant_ideas_has_required_fields(self, prediction_svc):
        dormant = prediction_svc.get_dormant_ideas(threshold=0.0)
        if dormant:
            d = dormant[0]
            assert "id" in d
            assert "dormancy_score" in d
            assert "reason" in d

    def test_old_ideas_score_higher(self, prediction_svc):
        """Ideas from 1800 should have higher dormancy than 2020 tech."""
        dormant = prediction_svc.get_dormant_ideas(threshold=0.0)
        scores = {d["id"]: d["dormancy_score"] for d in dormant}
        assert scores.get("philo_1800", 0) > scores.get("tech_2020", 0)

    def test_high_threshold_excludes_all(self, prediction_svc):
        dormant = prediction_svc.get_dormant_ideas(threshold=0.99)
        assert len(dormant) == 0

    def test_dormant_sorted_descending(self, prediction_svc):
        dormant = prediction_svc.get_dormant_ideas(threshold=0.0)
        scores = [d["dormancy_score"] for d in dormant]
        assert scores == sorted(scores, reverse=True)


# ─── Evolution Forecasting ───────────────────────────────────────

class TestEvolutionForecasting:
    def test_forecast_returns_required_fields(self, prediction_svc):
        f = prediction_svc.forecast_idea("philo_1800")
        assert "id" in f
        assert "current_stage" in f
        assert "predicted_next_stage" in f
        assert "confidence" in f
        assert "reason" in f
        assert "model" in f

    def test_forecast_confidence_in_range(self, prediction_svc):
        f = prediction_svc.forecast_idea("philo_1800")
        assert 0 <= f["confidence"] <= 1.0

    def test_forecast_invalid_id(self, prediction_svc):
        with pytest.raises(ValueError, match="not found"):
            prediction_svc.forecast_idea("does_not_exist")

    def test_forecast_tech_idea_stays_tech(self, prediction_svc):
        f = prediction_svc.forecast_idea("tech_2020")
        # Already at MODERN_TECHNOLOGY — predicts same or stays
        assert f["current_stage"] == "modern_technology"

    def test_forecast_reason_is_nonempty(self, prediction_svc):
        f = prediction_svc.forecast_idea("sci_1900")
        assert len(f["reason"]) > 0


# ─── Prediction Overview ────────────────────────────────────────

class TestPredictionOverview:
    def test_overview_has_required_keys(self, prediction_svc):
        overview = prediction_svc.get_prediction_overview()
        assert "total_ideas" in overview
        assert "dormant_count" in overview
        assert "dormant_ideas" in overview
        assert "forecasts" in overview
        assert "average_confidence" in overview

    def test_overview_total_matches(self, prediction_svc):
        overview = prediction_svc.get_prediction_overview()
        assert overview["total_ideas"] == 4

    def test_overview_forecasts_count(self, prediction_svc):
        overview = prediction_svc.get_prediction_overview()
        assert len(overview["forecasts"]) == 4


# ─── Empty Dataset Edge Cases ────────────────────────────────────

class TestEmptyDataset:
    def test_empty_dormant(self):
        s = DataStore(data_dir="data/_test_empty_ai")
        s.clear_all()
        g = LineageGraph()
        svc = AIPredictionService(s, g)
        assert svc.get_dormant_ideas() == []

    def test_empty_overview(self):
        s = DataStore(data_dir="data/_test_empty_ai2")
        s.clear_all()
        g = LineageGraph()
        svc = AIPredictionService(s, g)
        overview = svc.get_prediction_overview()
        assert overview["total_ideas"] == 0
