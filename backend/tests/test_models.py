"""
Unit tests for data models and validation.
"""

import pytest
from datetime import datetime

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.models.validation import validate_time_period


class TestEvolutionStage:
    """Tests for EvolutionStage enum."""
    
    def test_enum_values(self):
        """Test that all enum values are correct."""
        assert EvolutionStage.PHILOSOPHY.value == "philosophy"
        assert EvolutionStage.SCIENTIFIC_VALIDATION.value == "scientific_validation"
        assert EvolutionStage.ENGINEERING_APPLICATION.value == "engineering_application"
        assert EvolutionStage.MODERN_TECHNOLOGY.value == "modern_technology"
    
    def test_from_string_valid(self):
        """Test converting valid strings to enum."""
        assert EvolutionStage.from_string("philosophy") == EvolutionStage.PHILOSOPHY
        assert EvolutionStage.from_string("PHILOSOPHY") == EvolutionStage.PHILOSOPHY
        assert EvolutionStage.from_string("scientific_validation") == EvolutionStage.SCIENTIFIC_VALIDATION
    
    def test_from_string_invalid(self):
        """Test that invalid strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid evolution stage"):
            EvolutionStage.from_string("invalid_stage")


class TestIdeaNode:
    """Tests for IdeaNode model."""
    
    def test_valid_idea_node(self):
        """Test creating a valid IdeaNode."""
        idea = IdeaNode(
            id="quantum_mechanics_1925",
            title="Quantum Mechanics",
            description="Foundation of quantum theory",
            stage=EvolutionStage.PHILOSOPHY,
            start_year=1925,
            end_year=1950,
            category="Physics",
            laureates=["Heisenberg", "Schrödinger"],
            motivation="Revolutionized understanding of atomic behavior",
            keywords=["quantum", "mechanics", "physics"],
            influence_score=0.95
        )
        
        assert idea.id == "quantum_mechanics_1925"
        assert idea.stage == EvolutionStage.PHILOSOPHY
        assert idea.influence_score == 0.95
    
    def test_idea_node_empty_id(self):
        """Test that empty id raises ValueError."""
        with pytest.raises(ValueError, match="id must be non-empty"):
            IdeaNode(
                id="",
                title="Test",
                description="Test description",
                stage=EvolutionStage.PHILOSOPHY,
                start_year=2000,
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=["test"]
            )
    
    def test_idea_node_invalid_id_characters(self):
        """Test that id with invalid characters raises ValueError."""
        with pytest.raises(ValueError, match="alphanumeric characters and underscores"):
            IdeaNode(
                id="invalid-id-with-dashes",
                title="Test",
                description="Test description",
                stage=EvolutionStage.PHILOSOPHY,
                start_year=2000,
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=["test"]
            )
    
    def test_idea_node_invalid_start_year(self):
        """Test that invalid start_year raises ValueError."""
        with pytest.raises(ValueError, match="start_year must be between"):
            IdeaNode(
                id="test_id",
                title="Test",
                description="Test description",
                stage=EvolutionStage.PHILOSOPHY,
                start_year=1700,  # Too early
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=["test"]
            )
    
    def test_idea_node_invalid_end_year(self):
        """Test that end_year < start_year raises ValueError."""
        with pytest.raises(ValueError, match="end_year.*must be >= start_year"):
            IdeaNode(
                id="test_id",
                title="Test",
                description="Test description",
                stage=EvolutionStage.PHILOSOPHY,
                start_year=2000,
                end_year=1999,  # Before start_year
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=["test"]
            )
    
    def test_idea_node_invalid_influence_score(self):
        """Test that influence_score outside [0.0, 1.0] raises ValueError."""
        with pytest.raises(ValueError, match="influence_score must be between 0.0 and 1.0"):
            IdeaNode(
                id="test_id",
                title="Test",
                description="Test description",
                stage=EvolutionStage.PHILOSOPHY,
                start_year=2000,
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=["test"],
                influence_score=1.5  # Too high
            )
    
    def test_idea_node_empty_keywords(self):
        """Test that empty keywords list raises ValueError."""
        with pytest.raises(ValueError, match="keywords must contain at least one keyword"):
            IdeaNode(
                id="test_id",
                title="Test",
                description="Test description",
                stage=EvolutionStage.PHILOSOPHY,
                start_year=2000,
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=[]  # Empty
            )
    
    def test_idea_node_description_too_long(self):
        """Test that description over 10,000 characters raises ValueError."""
        with pytest.raises(ValueError, match="description must be at most 10,000 characters"):
            IdeaNode(
                id="test_id",
                title="Test",
                description="x" * 10001,  # Too long
                stage=EvolutionStage.PHILOSOPHY,
                start_year=2000,
                category="Test",
                laureates=["Test"],
                motivation="Test",
                keywords=["test"]
            )
    
    def test_idea_node_to_dict(self):
        """Test converting IdeaNode to dictionary."""
        idea = IdeaNode(
            id="test_id",
            title="Test",
            description="Test description",
            stage=EvolutionStage.PHILOSOPHY,
            start_year=2000,
            category="Test",
            laureates=["Test"],
            motivation="Test",
            keywords=["test"]
        )
        
        data = idea.to_dict()
        assert data['id'] == "test_id"
        assert data['stage'] == "philosophy"
        assert 'created_at' in data
    
    def test_idea_node_from_dict(self):
        """Test creating IdeaNode from dictionary."""
        data = {
            'id': "test_id",
            'title': "Test",
            'description': "Test description",
            'stage': "philosophy",
            'start_year': 2000,
            'end_year': None,
            'category': "Test",
            'laureates': ["Test"],
            'motivation': "Test",
            'keywords': ["test"],
            'influence_score': 0.5,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        idea = IdeaNode.from_dict(data)
        assert idea.id == "test_id"
        assert idea.stage == EvolutionStage.PHILOSOPHY


class TestInfluenceEdge:
    """Tests for InfluenceEdge model."""
    
    def test_valid_influence_edge(self):
        """Test creating a valid InfluenceEdge."""
        edge = InfluenceEdge(
            source_id="idea1",
            target_id="idea2",
            influence_type="derived_from",
            influence_weight=0.8,
            evidence="Clear derivation in literature",
            confidence_score=0.9
        )
        
        assert edge.source_id == "idea1"
        assert edge.target_id == "idea2"
        assert edge.influence_type == "derived_from"
    
    def test_influence_edge_self_loop(self):
        """Test that self-loops raise ValueError."""
        with pytest.raises(ValueError, match="no self-loops"):
            InfluenceEdge(
                source_id="idea1",
                target_id="idea1",  # Same as source
                influence_type="derived_from",
                influence_weight=0.8,
                evidence="Test",
                confidence_score=0.9
            )
    
    def test_influence_edge_invalid_type(self):
        """Test that invalid influence_type raises ValueError."""
        with pytest.raises(ValueError, match="influence_type must be one of"):
            InfluenceEdge(
                source_id="idea1",
                target_id="idea2",
                influence_type="invalid_type",
                influence_weight=0.8,
                evidence="Test",
                confidence_score=0.9
            )
    
    def test_influence_edge_invalid_weight(self):
        """Test that invalid influence_weight raises ValueError."""
        with pytest.raises(ValueError, match="influence_weight must be between 0.0 and 1.0"):
            InfluenceEdge(
                source_id="idea1",
                target_id="idea2",
                influence_type="derived_from",
                influence_weight=1.5,  # Too high
                evidence="Test",
                confidence_score=0.9
            )
    
    def test_influence_edge_invalid_confidence(self):
        """Test that invalid confidence_score raises ValueError."""
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            InfluenceEdge(
                source_id="idea1",
                target_id="idea2",
                influence_type="derived_from",
                influence_weight=0.8,
                evidence="Test",
                confidence_score=-0.1  # Too low
            )
    
    def test_influence_edge_empty_evidence(self):
        """Test that empty evidence raises ValueError."""
        with pytest.raises(ValueError, match="evidence must be non-empty"):
            InfluenceEdge(
                source_id="idea1",
                target_id="idea2",
                influence_type="derived_from",
                influence_weight=0.8,
                evidence="",  # Empty
                confidence_score=0.9
            )
    
    def test_influence_edge_to_dict(self):
        """Test converting InfluenceEdge to dictionary."""
        edge = InfluenceEdge(
            source_id="idea1",
            target_id="idea2",
            influence_type="derived_from",
            influence_weight=0.8,
            evidence="Test",
            confidence_score=0.9
        )
        
        data = edge.to_dict()
        assert data['source_id'] == "idea1"
        assert data['influence_type'] == "derived_from"
    
    def test_influence_edge_from_dict(self):
        """Test creating InfluenceEdge from dictionary."""
        data = {
            'source_id': "idea1",
            'target_id': "idea2",
            'influence_type': "derived_from",
            'influence_weight': 0.8,
            'evidence': "Test",
            'confidence_score': 0.9,
            'created_at': datetime.now().isoformat()
        }
        
        edge = InfluenceEdge.from_dict(data)
        assert edge.source_id == "idea1"
        assert edge.influence_type == "derived_from"


class TestValidation:
    """Tests for validation functions."""
    
    def test_validate_time_period_valid(self):
        """Test validating a valid time period."""
        # Should not raise
        validate_time_period(1900, 2000)
        validate_time_period(2000, 2000)  # Equal is valid
    
    def test_validate_time_period_invalid_order(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match="start_year.*must be <="):
            validate_time_period(2000, 1900)
    
    def test_validate_time_period_out_of_range(self):
        """Test that years outside [1800, 2200] raise ValueError."""
        with pytest.raises(ValueError, match="must be between 1800 and 2200"):
            validate_time_period(1700, 1900)
        
        with pytest.raises(ValueError, match="must be between 1800 and 2200"):
            validate_time_period(1900, 2300)
