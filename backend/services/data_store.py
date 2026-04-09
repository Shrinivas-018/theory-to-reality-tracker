"""
Data persistence layer for storing and retrieving ideas and influence edges.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage


class DataStore:
    """
    Simple file-based data store for ideas and influence edges.
    
    This implementation uses JSON files for persistence. For production,
    this could be replaced with a PostgreSQL database.
    """
    
    def __init__(self, data_dir: str = "data/evolution_tracker"):
        """
        Initialize the data store.
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.ideas_file = self.data_dir / "ideas.json"
        self.edges_file = self.data_dir / "edges.json"
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty data structures
        self._ideas: Dict[str, IdeaNode] = {}
        self._edges: List[InfluenceEdge] = []
        
        # Load existing data
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from JSON files."""
        # Load ideas
        if self.ideas_file.exists():
            with open(self.ideas_file, 'r', encoding='utf-8') as f:
                ideas_data = json.load(f)
                self._ideas = {
                    idea_id: IdeaNode.from_dict(idea_dict)
                    for idea_id, idea_dict in ideas_data.items()
                }
        
        # Load edges
        if self.edges_file.exists():
            with open(self.edges_file, 'r', encoding='utf-8') as f:
                edges_data = json.load(f)
                self._edges = [
                    InfluenceEdge.from_dict(edge_dict)
                    for edge_dict in edges_data
                ]
    
    def _save_data(self) -> None:
        """Save data to JSON files."""
        # Save ideas
        ideas_data = {
            idea_id: idea.to_dict()
            for idea_id, idea in self._ideas.items()
        }
        with open(self.ideas_file, 'w', encoding='utf-8') as f:
            json.dump(ideas_data, f, indent=2)
        
        # Save edges
        edges_data = [edge.to_dict() for edge in self._edges]
        with open(self.edges_file, 'w', encoding='utf-8') as f:
            json.dump(edges_data, f, indent=2)
    
    # Idea operations
    
    def add_idea(self, idea: IdeaNode) -> None:
        """
        Add a new idea to the store.
        
        Args:
            idea: IdeaNode to add
            
        Raises:
            ValueError: If idea with same id already exists
        """
        if idea.id in self._ideas:
            raise ValueError(f"Idea with id '{idea.id}' already exists")
        
        self._ideas[idea.id] = idea
        self._save_data()
    
    def get_idea(self, idea_id: str) -> Optional[IdeaNode]:
        """
        Get an idea by id.
        
        Args:
            idea_id: ID of the idea to retrieve
            
        Returns:
            IdeaNode if found, None otherwise
        """
        return self._ideas.get(idea_id)
    
    def update_idea(self, idea: IdeaNode) -> None:
        """
        Update an existing idea.
        
        Args:
            idea: IdeaNode with updated data
            
        Raises:
            ValueError: If idea doesn't exist
        """
        if idea.id not in self._ideas:
            raise ValueError(f"Idea with id '{idea.id}' not found")
        
        from datetime import datetime
        idea.updated_at = datetime.now()
        self._ideas[idea.id] = idea
        self._save_data()
    
    def delete_idea(self, idea_id: str) -> None:
        """
        Delete an idea from the store.
        
        Args:
            idea_id: ID of the idea to delete
            
        Raises:
            ValueError: If idea doesn't exist
        """
        if idea_id not in self._ideas:
            raise ValueError(f"Idea with id '{idea_id}' not found")
        
        del self._ideas[idea_id]
        
        # Also remove any edges referencing this idea
        self._edges = [
            edge for edge in self._edges
            if edge.source_id != idea_id and edge.target_id != idea_id
        ]
        
        self._save_data()
    
    def get_all_ideas(self) -> List[IdeaNode]:
        """
        Get all ideas in the store.
        
        Returns:
            List of all IdeaNode instances
        """
        return list(self._ideas.values())
    
    def get_ideas_by_stage(self, stage: EvolutionStage) -> List[IdeaNode]:
        """
        Get all ideas at a specific evolution stage.
        
        Args:
            stage: EvolutionStage to filter by
            
        Returns:
            List of IdeaNode instances at the specified stage
        """
        return [
            idea for idea in self._ideas.values()
            if idea.stage == stage
        ]
    
    # Edge operations
    
    def add_edge(self, edge: InfluenceEdge) -> None:
        """
        Add a new influence edge to the store.
        
        Args:
            edge: InfluenceEdge to add
            
        Raises:
            ValueError: If source or target idea doesn't exist
        """
        # Validate that both ideas exist
        if edge.source_id not in self._ideas:
            raise ValueError(f"Source idea '{edge.source_id}' not found")
        
        if edge.target_id not in self._ideas:
            raise ValueError(f"Target idea '{edge.target_id}' not found")
        
        self._edges.append(edge)
        self._save_data()
    
    def get_edges_from(self, source_id: str) -> List[InfluenceEdge]:
        """
        Get all edges originating from a specific idea.
        
        Args:
            source_id: ID of the source idea
            
        Returns:
            List of InfluenceEdge instances
        """
        return [
            edge for edge in self._edges
            if edge.source_id == source_id
        ]
    
    def get_edges_to(self, target_id: str) -> List[InfluenceEdge]:
        """
        Get all edges pointing to a specific idea.
        
        Args:
            target_id: ID of the target idea
            
        Returns:
            List of InfluenceEdge instances
        """
        return [
            edge for edge in self._edges
            if edge.target_id == target_id
        ]
    
    def get_all_edges(self) -> List[InfluenceEdge]:
        """
        Get all edges in the store.
        
        Returns:
            List of all InfluenceEdge instances
        """
        return self._edges.copy()
    
    def delete_edge(self, source_id: str, target_id: str) -> None:
        """
        Delete an influence edge.
        
        Args:
            source_id: ID of the source idea
            target_id: ID of the target idea
            
        Raises:
            ValueError: If edge doesn't exist
        """
        original_length = len(self._edges)
        self._edges = [
            edge for edge in self._edges
            if not (edge.source_id == source_id and edge.target_id == target_id)
        ]
        
        if len(self._edges) == original_length:
            raise ValueError(
                f"Edge from '{source_id}' to '{target_id}' not found"
            )
        
        self._save_data()
    
    # Utility methods
    
    def clear_all(self) -> None:
        """Clear all data from the store."""
        self._ideas.clear()
        self._edges.clear()
        self._save_data()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the data store.
        
        Returns:
            Dictionary with counts of ideas and edges
        """
        return {
            'total_ideas': len(self._ideas),
            'total_edges': len(self._edges),
            'ideas_by_stage': {
                stage.value: len(self.get_ideas_by_stage(stage))
                for stage in EvolutionStage
            }
        }
