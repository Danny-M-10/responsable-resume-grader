"""
Scoring Profile Data Structures
Defines industry-specific scoring templates and profiles
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class ScoringProfile:
    """Represents a scoring profile with weights and industry-specific rules"""
    name: str  # e.g., "healthcare", "technology", "construction"
    weights: Dict[str, float]  # Component weights (must sum to 1.0)
    required_criteria: List[str] = field(default_factory=list)  # Must-have criteria
    industry_specific_rules: Dict[str, Any] = field(default_factory=dict)  # Industry-specific logic
    description: str = ""  # Human-readable description of the profile


def get_default_weights() -> Dict[str, float]:
    """
    Returns the default (General/Universal) scoring weights.
    New priority order:
    1. Experience Level (25%)
    2. Job Title Match (20%)
    3. Required Skills (18%)
    4. Transferrable Skills (15%)
    5. Location (10%)
    6. Preferred Skills (7%)
    7. Certifications/Education (5%)
    """
    return {
        'experience_level': 0.25,
        'job_title_match': 0.20,
        'required_skills': 0.18,
        'transferrable_skills': 0.15,
        'location': 0.10,
        'preferred_skills': 0.07,
        'certifications_education': 0.05
    }


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that weights sum to approximately 1.0
    
    Args:
        weights: Dictionary of component weights
        
    Returns:
        True if weights are valid (sum to 1.0 within tolerance)
    """
    total = sum(weights.values())
    return abs(total - 1.0) < 0.01  # Allow small floating point errors

