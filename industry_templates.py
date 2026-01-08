"""
Industry Templates Module
Pre-configured scoring profiles for different industries
"""

from typing import Dict, List, Any
from scoring_profiles import ScoringProfile, get_default_weights


def get_industry_templates() -> Dict[str, ScoringProfile]:
    """
    Get all available industry templates
    
    Returns:
        Dictionary mapping template names to ScoringProfile objects
    """
    return {
        'general': get_general_template(),
        'healthcare': get_healthcare_template(),
        'technology': get_technology_template(),
        'construction': get_construction_template(),
        'finance': get_finance_template(),
        'sales': get_sales_template(),
    }


def get_general_template() -> ScoringProfile:
    """
    General/Universal template - universal standard for resume grading
    New priority order: Experience > Job Title > Required Skills > Transferrable Skills > Location > Preferred Skills > Certifications/Education
    This is the default template used when no industry-specific template is selected
    """
    return ScoringProfile(
        name='general',
        description='Universal standard - Prioritizes experience and job relevance. Balanced scoring suitable for most industries and roles (DEFAULT)',
        weights=get_default_weights(),  # Uses new default structure
        required_criteria=[],
        industry_specific_rules={}
    )


def get_healthcare_template() -> ScoringProfile:
    """
    Healthcare template - emphasizes experience, certifications, and licenses
    Adjusted to new structure while maintaining healthcare priorities (certs still important but lower priority)
    """
    return ScoringProfile(
        name='healthcare',
        description='Emphasizes experience and certifications/licenses. Ideal for medical, nursing, and healthcare roles.',
        weights={
            'experience_level': 0.28,  # Highest priority - experience matters
            'job_title_match': 0.20,  # Job title relevance important
            'required_skills': 0.18,  # Required clinical skills
            'transferrable_skills': 0.12,  # Cross-industry medical skills
            'location': 0.08,  # Location can matter for healthcare
            'preferred_skills': 0.07,  # Preferred skills
            'certifications_education': 0.07  # Certs/licenses still important but lower priority
        },
        required_criteria=['licenses', 'certifications'],
        industry_specific_rules={
            'skill_synonyms': {
                'medical': ['healthcare', 'clinical', 'patient care', 'nursing'],
                'license': ['certification', 'credential', 'registration'],
            },
            'common_certifications': [
                'RN', 'LPN', 'BLS', 'ACLS', 'CPR', 'HIPAA', 'OSHA',
                'Medical License', 'Nursing License', 'Board Certified'
            ]
        }
    )


def get_technology_template() -> ScoringProfile:
    """
    Technology template - emphasizes experience, skills, and transferrable technical abilities
    Experience and skills are more important than certifications in tech
    """
    return ScoringProfile(
        name='technology',
        description='Emphasizes experience, technical skills, and transferrable abilities. Ideal for software engineering, IT, and tech roles.',
        weights={
            'experience_level': 0.28,  # Highest priority - experience critical
            'job_title_match': 0.20,  # Job title relevance
            'required_skills': 0.22,  # Technical skills important
            'transferrable_skills': 0.18,  # Transferrable tech skills highly valued
            'location': 0.05,  # Location less important (remote work common)
            'preferred_skills': 0.05,  # Preferred skills
            'certifications_education': 0.02  # Certs least important in tech
        },
        required_criteria=['technical_skills'],
        industry_specific_rules={
            'skill_synonyms': {
                'programming': ['coding', 'development', 'software engineering'],
                'cloud': ['AWS', 'Azure', 'GCP', 'cloud computing'],
                'database': ['SQL', 'NoSQL', 'data management'],
            },
            'common_certifications': [
                'AWS Certified', 'Microsoft Certified', 'Google Cloud Certified',
                'CISSP', 'PMP', 'Scrum Master', 'Agile Certified'
            ]
        }
    )


def get_construction_template() -> ScoringProfile:
    """
    Construction/Safety template - emphasizes experience, certifications, and hands-on skills
    Adjusted to new structure while maintaining safety priorities
    """
    return ScoringProfile(
        name='construction',
        description='Emphasizes hands-on experience, safety certifications, and transferrable trade skills. Ideal for construction, safety, and trade roles.',
        weights={
            'experience_level': 0.30,  # Highest priority - hands-on experience critical
            'job_title_match': 0.20,  # Job title relevance
            'required_skills': 0.18,  # Required trade skills
            'transferrable_skills': 0.15,  # Transferrable trade/construction skills
            'location': 0.08,  # Location can matter for construction
            'preferred_skills': 0.05,  # Preferred skills
            'certifications_education': 0.04  # Safety certs important but lower priority
        },
        required_criteria=['safety_certifications', 'licenses'],
        industry_specific_rules={
            'skill_synonyms': {
                'safety': ['OSHA', 'safety management', 'hazard identification'],
                'construction': ['building', 'trade', 'craftsman'],
                'equipment': ['machinery', 'tools', 'operation'],
            },
            'common_certifications': [
                'OSHA 10', 'OSHA 30', 'CDL', 'Crane Operator', 'Forklift',
                'First Aid', 'CPR', 'Confined Space', 'Fall Protection'
            ]
        }
    )


def get_finance_template() -> ScoringProfile:
    """
    Finance template - emphasizes experience, education, and certifications
    Adjusted to new structure while maintaining finance priorities
    """
    return ScoringProfile(
        name='finance',
        description='Emphasizes experience, education, and financial certifications. Ideal for accounting, banking, and finance roles.',
        weights={
            'experience_level': 0.28,  # Highest priority - experience critical
            'job_title_match': 0.20,  # Job title relevance
            'required_skills': 0.18,  # Required financial skills
            'transferrable_skills': 0.12,  # Transferrable analytical/business skills
            'location': 0.08,  # Location can matter for finance
            'preferred_skills': 0.07,  # Preferred skills
            'certifications_education': 0.07  # Certs/education important but lower priority
        },
        required_criteria=['financial_certifications', 'education'],
        industry_specific_rules={
            'skill_synonyms': {
                'accounting': ['bookkeeping', 'financial reporting', 'GAAP'],
                'analysis': ['financial analysis', 'forecasting', 'modeling'],
                'compliance': ['regulatory', 'audit', 'SOX'],
            },
            'common_certifications': [
                'CPA', 'CFA', 'CMA', 'Series 7', 'Series 63', 'FRM',
                'CIA', 'CISA', 'CFP'
            ]
        }
    )


def get_sales_template() -> ScoringProfile:
    """
    Sales template - emphasizes experience, job title match, and transferrable skills
    Sales success is more about experience and soft skills than certifications
    """
    return ScoringProfile(
        name='sales',
        description='Emphasizes experience, job title relevance, and transferrable skills. Ideal for sales, account management, and business development roles.',
        weights={
            'experience_level': 0.30,  # Highest priority - experience critical
            'job_title_match': 0.22,  # Job title relevance very important
            'required_skills': 0.18,  # Required sales skills
            'transferrable_skills': 0.15,  # Transferrable communication/relationship skills
            'location': 0.08,  # Location can matter for sales
            'preferred_skills': 0.05,  # Preferred skills
            'certifications_education': 0.02  # Certs least important in sales
        },
        required_criteria=['experience', 'soft_skills'],
        industry_specific_rules={
            'skill_synonyms': {
                'sales': ['business development', 'account management', 'revenue generation'],
                'communication': ['negotiation', 'presentation', 'relationship building'],
                'achievement': ['quota', 'target', 'performance'],
            },
            'common_certifications': [
                'Salesforce Certified', 'HubSpot Certified', 'SPIN Selling',
                'Challenger Sale', 'Sandler Training'
            ]
        }
    )


def get_template_by_name(name: str) -> ScoringProfile:
    """
    Get a specific template by name
    
    Args:
        name: Template name (e.g., 'healthcare', 'technology')
        
    Returns:
        ScoringProfile object
        
    Raises:
        ValueError: If template name is not found
    """
    templates = get_industry_templates()
    name_lower = name.lower()
    
    if name_lower not in templates:
        available = ', '.join(templates.keys())
        raise ValueError(f"Template '{name}' not found. Available templates: {available}")
    
    return templates[name_lower]


# Note: validate_weights and get_default_weights are now in scoring_profiles.py

