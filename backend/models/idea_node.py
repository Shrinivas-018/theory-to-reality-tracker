"""
IdeaNode data model representing an idea in the evolution tracker.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from .evolution_stage import EvolutionStage


@dataclass
class IdeaNode:
    """
    Represents an idea with its metadata and evolution information.
    
    Attributes:
        id: Unique identifier for the idea
        title: Title of the idea
        description: Detailed description of the idea
        stage: Current evolution stage
        start_year: Year the idea was introduced
        end_year: Year the idea reached its current stage (optional)
        category: Category classification (e.g., "Physics", "Chemistry")
        laureates: List of people associated with the idea
        motivation: Motivation or reasoning behind the idea
        keywords: List of keywords describing the idea
        influence_score: Influence score between 0.0 and 1.0
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """
    id: str
    title: str
    description: str
    stage: EvolutionStage
    start_year: int
    category: str
    laureates: List[str]
    motivation: str
    keywords: List[str]
    influence_score: float = 0.0
    end_year: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate the IdeaNode after initialization."""
        from .validation import validate_idea_node
        validate_idea_node(self)
    
    def to_dict(self) -> dict:
        """
        Convert IdeaNode to dictionary representation.
        
        Returns:
            Dictionary with all IdeaNode fields
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'stage': self.stage.value,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'category': self.category,
            'laureates': self.laureates,
            'motivation': self.motivation,
            'keywords': self.keywords,
            'influence_score': self.influence_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'IdeaNode':
        """
        Create IdeaNode from dictionary representation.
        
        Args:
            data: Dictionary with IdeaNode fields
            
        Returns:
            IdeaNode instance
        """
        # Convert stage string to enum
        if isinstance(data.get('stage'), str):
            data['stage'] = EvolutionStage.from_string(data['stage'])
        
        # Convert datetime strings to datetime objects
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
