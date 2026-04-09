"""
Validation functions for data models.
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .idea_node import IdeaNode
    from .influence_edge import InfluenceEdge


def validate_idea_node(idea: 'IdeaNode') -> None:
    """
    Validate IdeaNode according to requirements 15.1-15.6.
    
    Args:
        idea: IdeaNode instance to validate
        
    Raises:
        ValueError: If validation fails
    """
    # Requirement 15.1: id must be unique and non-empty
    if not idea.id or not idea.id.strip():
        raise ValueError("IdeaNode id must be non-empty")
    
    # Sanitize id to alphanumeric and underscores only (Requirement 19.1)
    if not re.match(r'^[a-zA-Z0-9_]+$', idea.id):
        raise ValueError(
            "IdeaNode id must contain only alphanumeric characters and underscores"
        )
    
    # Requirement 15.2: start_year must be between 1800 and current year + 100
    current_year = datetime.now().year
    if not (1800 <= idea.start_year <= current_year + 100):
        raise ValueError(
            f"IdeaNode start_year must be between 1800 and {current_year + 100}, "
            f"got {idea.start_year}"
        )
    
    # Requirement 15.3: end_year must be >= start_year if provided
    if idea.end_year is not None:
        if idea.end_year < idea.start_year:
            raise ValueError(
                f"IdeaNode end_year ({idea.end_year}) must be >= "
                f"start_year ({idea.start_year})"
            )
        
        # Also validate end_year is in valid range (Requirement 14.4)
        if not (1800 <= idea.end_year <= 2200):
            raise ValueError(
                f"IdeaNode end_year must be between 1800 and 2200, "
                f"got {idea.end_year}"
            )
    
    # Requirement 15.4: stage must be valid EvolutionStage enum value
    from .evolution_stage import EvolutionStage
    if not isinstance(idea.stage, EvolutionStage):
        raise ValueError(
            f"IdeaNode stage must be an EvolutionStage enum, "
            f"got {type(idea.stage)}"
        )
    
    # Requirement 15.5: influence_score must be between 0.0 and 1.0
    if not (0.0 <= idea.influence_score <= 1.0):
        raise ValueError(
            f"IdeaNode influence_score must be between 0.0 and 1.0, "
            f"got {idea.influence_score}"
        )
    
    # Requirement 15.6: keywords must contain at least one keyword
    if not idea.keywords or len(idea.keywords) == 0:
        raise ValueError("IdeaNode keywords must contain at least one keyword")
    
    # Validate title is non-empty
    if not idea.title or not idea.title.strip():
        raise ValueError("IdeaNode title must be non-empty")
    
    # Requirement 19.2: description length limit
    if len(idea.description) > 10000:
        raise ValueError(
            f"IdeaNode description must be at most 10,000 characters, "
            f"got {len(idea.description)}"
        )
    
    # Validate category is non-empty
    if not idea.category or not idea.category.strip():
        raise ValueError("IdeaNode category must be non-empty")
    
    # Validate motivation is non-empty
    if not idea.motivation or not idea.motivation.strip():
        raise ValueError("IdeaNode motivation must be non-empty")


def validate_influence_edge(edge: 'InfluenceEdge') -> None:
    """
    Validate InfluenceEdge according to requirements 15.7-15.9.
    
    Args:
        edge: InfluenceEdge instance to validate
        
    Raises:
        ValueError: If validation fails
    """
    # Validate source_id and target_id are non-empty
    if not edge.source_id or not edge.source_id.strip():
        raise ValueError("InfluenceEdge source_id must be non-empty")
    
    if not edge.target_id or not edge.target_id.strip():
        raise ValueError("InfluenceEdge target_id must be non-empty")
    
    # Requirement 13.5: Prevent self-loops
    if edge.source_id == edge.target_id:
        raise ValueError(
            "InfluenceEdge cannot have source_id equal to target_id (no self-loops)"
        )
    
    # Requirement 15.9: influence_type must be one of valid types
    if edge.influence_type not in edge.VALID_INFLUENCE_TYPES:
        raise ValueError(
            f"InfluenceEdge influence_type must be one of "
            f"{edge.VALID_INFLUENCE_TYPES}, got '{edge.influence_type}'"
        )
    
    # Requirement 15.7: influence_weight must be between 0.0 and 1.0
    if not (0.0 <= edge.influence_weight <= 1.0):
        raise ValueError(
            f"InfluenceEdge influence_weight must be between 0.0 and 1.0, "
            f"got {edge.influence_weight}"
        )
    
    # Requirement 15.8: confidence_score must be between 0.0 and 1.0
    if not (0.0 <= edge.confidence_score <= 1.0):
        raise ValueError(
            f"InfluenceEdge confidence_score must be between 0.0 and 1.0, "
            f"got {edge.confidence_score}"
        )
    
    # Validate evidence is non-empty
    if not edge.evidence or not edge.evidence.strip():
        raise ValueError("InfluenceEdge evidence must be non-empty")


def validate_time_period(start_year: int, end_year: int) -> None:
    """
    Validate time period according to requirements 14.3-14.4.
    
    Args:
        start_year: Start year of the period
        end_year: End year of the period
        
    Raises:
        ValueError: If validation fails
    """
    # Requirement 14.3: start_year must be <= end_year
    if start_year > end_year:
        raise ValueError(
            f"Invalid time range: start_year ({start_year}) must be <= "
            f"end_year ({end_year})"
        )
    
    # Requirement 14.4: years must be between 1800 and 2200
    if not (1800 <= start_year <= 2200):
        raise ValueError(
            f"start_year must be between 1800 and 2200, got {start_year}"
        )
    
    if not (1800 <= end_year <= 2200):
        raise ValueError(
            f"end_year must be between 1800 and 2200, got {end_year}"
        )
