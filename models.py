"""
Data Models for Candidate Ranker Application
Shared dataclasses used across modules
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Certification:
    """Represents a certification requirement"""
    name: str
    category: str  # 'must-have' or 'bonus'


@dataclass
class JobDetails:
    """Structured job information"""
    job_title: str
    certifications: List[Certification]
    location: str
    full_description: str

    # Derived fields
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    experience_level: str = ""
    industry_context: str = ""
    soft_skills: List[str] = field(default_factory=list)
    technical_stack: List[str] = field(default_factory=list)
    equivalent_titles: List[str] = field(default_factory=list)
    skill_synonyms: Dict[str, List[str]] = field(default_factory=dict)
    certification_equivalents: Dict[str, List[str]] = field(default_factory=dict)  # Maps cert name to list of equivalents
    
    # Universal recruiting tool enhancements
    scoring_profile: Dict[str, float] = field(default_factory=dict)  # Custom scoring weights
    industry_template: str = ""  # Industry template name (e.g., "healthcare", "technology")
    custom_criteria: List[Dict[str, Any]] = field(default_factory=list)  # Additional custom evaluation criteria
    bias_reduction_enabled: bool = False  # Enable blind screening
    dealbreakers: List[str] = field(default_factory=list)  # Criteria that automatically disqualify candidates


@dataclass
class CandidateScore:
    """Represents a candidate's evaluation"""
    name: str
    phone: str
    email: str
    certifications: List[str]
    fit_score: float
    chain_of_thought: str
    rationale: str
    experience_match: Dict[str, Any]
    certification_match: Dict[str, Any]
    skills_match: Dict[str, Any]
    location_match: bool
    # Transferrable skills analysis (NEW)
    transferrable_skills_match: Dict[str, Any] = field(default_factory=lambda: {
        'match_rate': 0.0,
        'transferrable_skills': [],
        'relevance_score': 0.0
    })
    # Component scores for transparency and validation
    component_scores: Dict[str, float] = field(default_factory=dict)
    # Calibration metadata
    calibration_applied: bool = False
    calibration_factor: float = 1.0
