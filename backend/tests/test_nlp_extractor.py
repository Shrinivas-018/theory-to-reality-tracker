"""
Tests for the NLP Extractor Service.

Covers keyword extraction, named entity recognition,
stage classification, and batch analysis.
"""

import pytest
from backend.models import IdeaNode, EvolutionStage
from backend.services.data_store import DataStore
from backend.services.nlp_extractor import NLPExtractorService


@pytest.fixture
def temp_store(tmp_path):
    return DataStore(data_dir=str(tmp_path / "test_nlp"))


def _idea(id, title, desc, stage, year, keywords=None):
    return IdeaNode(
        id=id, title=title, description=desc,
        stage=stage, start_year=year,
        category="Physics", laureates=["Test"],
        motivation="Test motivation",
        keywords=keywords or ["test"],
        influence_score=0.5,
    )


@pytest.fixture
def seeded(temp_store):
    ideas = [
        _idea("p1", "Quantum Theory", "Theoretical framework for atomic physics",
              EvolutionStage.PHILOSOPHY, 1925, ["quantum", "theory", "physics"]),
        _idea("s1", "Nuclear Experiment", "Laboratory validation of nuclear fission",
              EvolutionStage.SCIENTIFIC_VALIDATION, 1938, ["nuclear", "experiment"]),
        _idea("e1", "Applied Engineering", "Engineering design for power systems",
              EvolutionStage.ENGINEERING_APPLICATION, 1960, ["engineering", "design"]),
        _idea("t1", "Modern Technology Product", "Global commercial technology platform",
              EvolutionStage.MODERN_TECHNOLOGY, 2020, ["technology", "commercial"]),
    ]
    for idea in ideas:
        temp_store.add_idea(idea)
    return temp_store


@pytest.fixture
def nlp_svc(seeded):
    return NLPExtractorService(seeded)


class TestKeywordExtraction:
    def test_extracts_keywords(self, nlp_svc):
        kws = nlp_svc.extract_keywords("quantum physics theory atomic", top_n=3)
        assert isinstance(kws, list)
        assert len(kws) <= 3

    def test_keyword_has_score(self, nlp_svc):
        kws = nlp_svc.extract_keywords("quantum physics", top_n=1)
        if kws:
            assert "keyword" in kws[0]
            assert "tfidf_score" in kws[0]

    def test_extract_for_idea(self, nlp_svc):
        kws = nlp_svc.extract_keywords_for_idea("p1", top_n=3)
        assert isinstance(kws, list)

    def test_extract_for_invalid_idea(self, nlp_svc):
        with pytest.raises(ValueError, match="not found"):
            nlp_svc.extract_keywords_for_idea("nonexistent")


class TestEntityExtraction:
    def test_finds_proper_nouns(self, nlp_svc):
        result = nlp_svc.extract_entities("Albert Einstein developed General Relativity at Princeton University")
        assert isinstance(result, dict)
        assert "persons" in result
        assert "organizations" in result
        assert "topics" in result

    def test_recognizes_org(self, nlp_svc):
        result = nlp_svc.extract_entities("NASA launched Apollo missions")
        # Should detect NASA as organization
        all_entities = result["persons"] + result["organizations"] + result["topics"]
        assert len(all_entities) > 0


class TestStageClassification:
    def test_classify_philosophy(self, nlp_svc):
        result = nlp_svc.classify_stage("A theoretical framework and philosophical hypothesis about nature")
        assert "predicted_stage" in result
        assert "confidence" in result
        assert "stage_scores" in result

    def test_classify_tech(self, nlp_svc):
        result = nlp_svc.classify_stage("Modern commercial technology platform for global production at scale")
        assert result["predicted_stage"] == "modern_technology"

    def test_stage_scores_sum(self, nlp_svc):
        result = nlp_svc.classify_stage("An experimental validation proving the theory correct")
        total = sum(result["stage_scores"].values())
        assert abs(total - 1.0) < 0.01  # should sum to ~1.0


class TestBatchAnalysis:
    def test_analyze_all(self, nlp_svc):
        results = nlp_svc.analyze_all_ideas()
        assert len(results) == 4

    def test_analysis_has_fields(self, nlp_svc):
        results = nlp_svc.analyze_all_ideas()
        for r in results:
            assert "id" in r
            assert "extracted_keywords" in r
            assert "predicted_stage" in r
            assert "stage_match" in r

    def test_empty_dataset(self, tmp_path):
        s = DataStore(data_dir=str(tmp_path / "empty_nlp"))
        svc = NLPExtractorService(s)
        assert svc.analyze_all_ideas() == []
