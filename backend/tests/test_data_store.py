"""
Unit tests for DataStore.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def data_store(temp_data_dir):
    """Create a DataStore instance with temporary directory."""
    return DataStore(data_dir=temp_data_dir)


@pytest.fixture
def sample_idea():
    """Create a sample IdeaNode for testing."""
    return IdeaNode(
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


@pytest.fixture
def sample_edge():
    """Create a sample InfluenceEdge for testing."""
    return InfluenceEdge(
        source_id="quantum_mechanics_1925",
        target_id="quantum_computing_2020",
        influence_type="derived_from",
        influence_weight=0.8,
        evidence="Quantum computing is based on quantum mechanics principles",
        confidence_score=0.95
    )


class TestDataStoreIdeas:
    """Tests for DataStore idea operations."""
    
    def test_add_idea(self, data_store, sample_idea):
        """Test adding an idea to the store."""
        data_store.add_idea(sample_idea)
        
        retrieved = data_store.get_idea(sample_idea.id)
        assert retrieved is not None
        assert retrieved.id == sample_idea.id
        assert retrieved.title == sample_idea.title
    
    def test_add_duplicate_idea(self, data_store, sample_idea):
        """Test that adding duplicate idea raises ValueError."""
        data_store.add_idea(sample_idea)
        
        with pytest.raises(ValueError, match="already exists"):
            data_store.add_idea(sample_idea)
    
    def test_get_nonexistent_idea(self, data_store):
        """Test getting a non-existent idea returns None."""
        result = data_store.get_idea("nonexistent_id")
        assert result is None
    
    def test_update_idea(self, data_store, sample_idea):
        """Test updating an existing idea."""
        data_store.add_idea(sample_idea)
        
        # Update the idea
        sample_idea.title = "Updated Title"
        data_store.update_idea(sample_idea)
        
        retrieved = data_store.get_idea(sample_idea.id)
        assert retrieved.title == "Updated Title"
    
    def test_update_nonexistent_idea(self, data_store, sample_idea):
        """Test that updating non-existent idea raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            data_store.update_idea(sample_idea)
    
    def test_delete_idea(self, data_store, sample_idea):
        """Test deleting an idea."""
        data_store.add_idea(sample_idea)
        data_store.delete_idea(sample_idea.id)
        
        result = data_store.get_idea(sample_idea.id)
        assert result is None
    
    def test_delete_nonexistent_idea(self, data_store):
        """Test that deleting non-existent idea raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            data_store.delete_idea("nonexistent_id")
    
    def test_get_all_ideas(self, data_store, sample_idea):
        """Test getting all ideas."""
        data_store.add_idea(sample_idea)
        
        idea2 = IdeaNode(
            id="relativity_1905",
            title="Theory of Relativity",
            description="Einstein's theory",
            stage=EvolutionStage.SCIENTIFIC_VALIDATION,
            start_year=1905,
            category="Physics",
            laureates=["Einstein"],
            motivation="Revolutionized physics",
            keywords=["relativity", "physics"]
        )
        data_store.add_idea(idea2)
        
        all_ideas = data_store.get_all_ideas()
        assert len(all_ideas) == 2
        assert any(idea.id == sample_idea.id for idea in all_ideas)
        assert any(idea.id == idea2.id for idea in all_ideas)
    
    def test_get_ideas_by_stage(self, data_store, sample_idea):
        """Test filtering ideas by stage."""
        data_store.add_idea(sample_idea)
        
        idea2 = IdeaNode(
            id="relativity_1905",
            title="Theory of Relativity",
            description="Einstein's theory",
            stage=EvolutionStage.SCIENTIFIC_VALIDATION,
            start_year=1905,
            category="Physics",
            laureates=["Einstein"],
            motivation="Revolutionized physics",
            keywords=["relativity", "physics"]
        )
        data_store.add_idea(idea2)
        
        philosophy_ideas = data_store.get_ideas_by_stage(EvolutionStage.PHILOSOPHY)
        assert len(philosophy_ideas) == 1
        assert philosophy_ideas[0].id == sample_idea.id
        
        science_ideas = data_store.get_ideas_by_stage(EvolutionStage.SCIENTIFIC_VALIDATION)
        assert len(science_ideas) == 1
        assert science_ideas[0].id == idea2.id


class TestDataStoreEdges:
    """Tests for DataStore edge operations."""
    
    def test_add_edge(self, data_store, sample_idea, sample_edge):
        """Test adding an edge to the store."""
        # Add both ideas first
        data_store.add_idea(sample_idea)
        
        target_idea = IdeaNode(
            id="quantum_computing_2020",
            title="Quantum Computing",
            description="Modern quantum computers",
            stage=EvolutionStage.MODERN_TECHNOLOGY,
            start_year=2020,
            category="Computer Science",
            laureates=["Various"],
            motivation="Practical quantum computation",
            keywords=["quantum", "computing"]
        )
        data_store.add_idea(target_idea)
        
        # Add edge
        data_store.add_edge(sample_edge)
        
        edges = data_store.get_edges_from(sample_edge.source_id)
        assert len(edges) == 1
        assert edges[0].source_id == sample_edge.source_id
        assert edges[0].target_id == sample_edge.target_id
    
    def test_add_edge_missing_source(self, data_store, sample_edge):
        """Test that adding edge with missing source raises ValueError."""
        with pytest.raises(ValueError, match="Source idea.*not found"):
            data_store.add_edge(sample_edge)
    
    def test_add_edge_missing_target(self, data_store, sample_idea, sample_edge):
        """Test that adding edge with missing target raises ValueError."""
        data_store.add_idea(sample_idea)
        
        with pytest.raises(ValueError, match="Target idea.*not found"):
            data_store.add_edge(sample_edge)
    
    def test_get_edges_from(self, data_store, sample_idea, sample_edge):
        """Test getting edges from a specific idea."""
        # Setup
        data_store.add_idea(sample_idea)
        target_idea = IdeaNode(
            id="quantum_computing_2020",
            title="Quantum Computing",
            description="Modern quantum computers",
            stage=EvolutionStage.MODERN_TECHNOLOGY,
            start_year=2020,
            category="Computer Science",
            laureates=["Various"],
            motivation="Practical quantum computation",
            keywords=["quantum", "computing"]
        )
        data_store.add_idea(target_idea)
        data_store.add_edge(sample_edge)
        
        edges = data_store.get_edges_from(sample_idea.id)
        assert len(edges) == 1
        assert edges[0].target_id == target_idea.id
    
    def test_get_edges_to(self, data_store, sample_idea, sample_edge):
        """Test getting edges to a specific idea."""
        # Setup
        data_store.add_idea(sample_idea)
        target_idea = IdeaNode(
            id="quantum_computing_2020",
            title="Quantum Computing",
            description="Modern quantum computers",
            stage=EvolutionStage.MODERN_TECHNOLOGY,
            start_year=2020,
            category="Computer Science",
            laureates=["Various"],
            motivation="Practical quantum computation",
            keywords=["quantum", "computing"]
        )
        data_store.add_idea(target_idea)
        data_store.add_edge(sample_edge)
        
        edges = data_store.get_edges_to(target_idea.id)
        assert len(edges) == 1
        assert edges[0].source_id == sample_idea.id
    
    def test_delete_edge(self, data_store, sample_idea, sample_edge):
        """Test deleting an edge."""
        # Setup
        data_store.add_idea(sample_idea)
        target_idea = IdeaNode(
            id="quantum_computing_2020",
            title="Quantum Computing",
            description="Modern quantum computers",
            stage=EvolutionStage.MODERN_TECHNOLOGY,
            start_year=2020,
            category="Computer Science",
            laureates=["Various"],
            motivation="Practical quantum computation",
            keywords=["quantum", "computing"]
        )
        data_store.add_idea(target_idea)
        data_store.add_edge(sample_edge)
        
        # Delete edge
        data_store.delete_edge(sample_edge.source_id, sample_edge.target_id)
        
        edges = data_store.get_edges_from(sample_edge.source_id)
        assert len(edges) == 0
    
    def test_delete_nonexistent_edge(self, data_store):
        """Test that deleting non-existent edge raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            data_store.delete_edge("source", "target")
    
    def test_delete_idea_cascades_to_edges(self, data_store, sample_idea, sample_edge):
        """Test that deleting an idea also removes its edges."""
        # Setup
        data_store.add_idea(sample_idea)
        target_idea = IdeaNode(
            id="quantum_computing_2020",
            title="Quantum Computing",
            description="Modern quantum computers",
            stage=EvolutionStage.MODERN_TECHNOLOGY,
            start_year=2020,
            category="Computer Science",
            laureates=["Various"],
            motivation="Practical quantum computation",
            keywords=["quantum", "computing"]
        )
        data_store.add_idea(target_idea)
        data_store.add_edge(sample_edge)
        
        # Delete source idea
        data_store.delete_idea(sample_idea.id)
        
        # Edge should be gone
        all_edges = data_store.get_all_edges()
        assert len(all_edges) == 0


class TestDataStorePersistence:
    """Tests for DataStore persistence."""
    
    def test_persistence_across_instances(self, temp_data_dir, sample_idea):
        """Test that data persists across DataStore instances."""
        # Create first instance and add data
        store1 = DataStore(data_dir=temp_data_dir)
        store1.add_idea(sample_idea)
        
        # Create second instance and verify data is loaded
        store2 = DataStore(data_dir=temp_data_dir)
        retrieved = store2.get_idea(sample_idea.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_idea.id
        assert retrieved.title == sample_idea.title
    
    def test_get_stats(self, data_store, sample_idea):
        """Test getting statistics about the data store."""
        data_store.add_idea(sample_idea)
        
        stats = data_store.get_stats()
        assert stats['total_ideas'] == 1
        assert stats['total_edges'] == 0
        assert stats['ideas_by_stage']['philosophy'] == 1
    
    def test_clear_all(self, data_store, sample_idea):
        """Test clearing all data."""
        data_store.add_idea(sample_idea)
        data_store.clear_all()
        
        all_ideas = data_store.get_all_ideas()
        assert len(all_ideas) == 0
        
        stats = data_store.get_stats()
        assert stats['total_ideas'] == 0
