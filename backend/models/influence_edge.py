"""
InfluenceEdge data model representing influence relationships between ideas.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InfluenceEdge:
    """
    Represents an influence relationship between two ideas.
    
    Attributes:
        source_id: ID of the idea that influenced
        target_id: ID of the idea that was influenced
        influence_type: Type of influence (derived_from, inspired_by, applied_to, validated_by)
        influence_weight: Weight of influence between 0.0 and 1.0
        evidence: Evidence supporting the influence relationship
        confidence_score: Confidence in the relationship between 0.0 and 1.0
        created_at: Timestamp when the edge was created
    """
    source_id: str
    target_id: str
    influence_type: str
    influence_weight: float
    evidence: str
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.now)
    
    # Valid influence types
    VALID_INFLUENCE_TYPES = {
        "derived_from",
        "inspired_by",
        "applied_to",
        "validated_by"
    }
    
    def __post_init__(self):
        """Validate the InfluenceEdge after initialization."""
        from .validation import validate_influence_edge
        validate_influence_edge(self)
    
    def to_dict(self) -> dict:
        """
        Convert InfluenceEdge to dictionary representation.
        
        Returns:
            Dictionary with all InfluenceEdge fields
        """
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'influence_type': self.influence_type,
            'influence_weight': self.influence_weight,
            'evidence': self.evidence,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'InfluenceEdge':
        """
        Create InfluenceEdge from dictionary representation.
        
        Args:
            data: Dictionary with InfluenceEdge fields
            
        Returns:
            InfluenceEdge instance
        """
        # Convert datetime string to datetime object
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
