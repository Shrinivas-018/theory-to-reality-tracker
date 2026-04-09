"""
Evolution stage enumeration for idea classification.
"""

from enum import Enum


class EvolutionStage(Enum):
    """
    Represents the four stages of idea evolution from philosophy to technology.
    """
    PHILOSOPHY = "philosophy"
    SCIENTIFIC_VALIDATION = "scientific_validation"
    ENGINEERING_APPLICATION = "engineering_application"
    MODERN_TECHNOLOGY = "modern_technology"
    
    @classmethod
    def from_string(cls, stage_str: str) -> 'EvolutionStage':
        """
        Convert string to EvolutionStage enum.
        
        Args:
            stage_str: String representation of stage
            
        Returns:
            EvolutionStage enum value
            
        Raises:
            ValueError: If stage_str is not a valid stage
        """
        stage_map = {
            "philosophy": cls.PHILOSOPHY,
            "scientific_validation": cls.SCIENTIFIC_VALIDATION,
            "engineering_application": cls.ENGINEERING_APPLICATION,
            "modern_technology": cls.MODERN_TECHNOLOGY
        }
        
        stage_str_lower = stage_str.lower()
        if stage_str_lower not in stage_map:
            raise ValueError(
                f"Invalid evolution stage: {stage_str}. "
                f"Must be one of: {', '.join(stage_map.keys())}"
            )
        
        return stage_map[stage_str_lower]
    
    def __str__(self) -> str:
        return self.value
