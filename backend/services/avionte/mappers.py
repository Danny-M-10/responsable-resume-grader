"""
Field mapping definitions between internal models and Avionté models
"""
from typing import Dict, Any, Optional, List


# Field mapping dictionaries
TALENT_FIELD_MAP = {
    # Internal field -> Avionté field
    "id": "talentId",
    "name": ["firstName", "lastName"],  # Split name
    "email": "email",
    "phone": "phone",
    "mobile": "mobile",
    "address": "address",
    "skills": "skills",
    "certifications": "certifications",
    "work_history": "workHistory",
    "education": "education",
    "resume_file": "documents",
    "status": "status",
    "tags": "tags",
}

JOB_FIELD_MAP = {
    # Internal field -> Avionté field
    "id": "jobId",
    "title": "jobTitle",
    "description": "description",
    "location": "location",
    "address": "address",
    "required_skills": "requiredSkills",
    "certifications": "requiredCertifications",
    "employment_type": "employmentType",
    "status": "status",
    "company_id": "companyId",
    "branch_id": "branchId",
}

# Reverse mappings (Avionté -> Internal)
TALENT_FIELD_MAP_REVERSE = {v: k for k, v in TALENT_FIELD_MAP.items() if isinstance(v, str)}
JOB_FIELD_MAP_REVERSE = {v: k for k, v in JOB_FIELD_MAP.items() if isinstance(v, str)}


def map_talent_name_to_avionte(name: str) -> Dict[str, str]:
    """
    Split full name into firstName and lastName
    
    Args:
        name: Full name string
        
    Returns:
        Dictionary with firstName and lastName
    """
    parts = name.strip().split(maxsplit=1)
    if len(parts) == 1:
        return {"firstName": parts[0], "lastName": ""}
    return {"firstName": parts[0], "lastName": parts[1]}


def map_avionte_name_to_internal(first_name: Optional[str], last_name: Optional[str]) -> str:
    """
    Combine firstName and lastName into full name
    
    Args:
        first_name: First name
        last_name: Last name
        
    Returns:
        Full name string
    """
    parts = [p for p in [first_name, last_name] if p]
    return " ".join(parts) if parts else ""


def map_skill_to_avionte(skill: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map internal skill format to Avionté skill format
    
    Args:
        skill: Internal skill dictionary
        
    Returns:
        Avionté skill dictionary
    """
    return {
        "name": skill.get("name", ""),
        "category": skill.get("category"),
        "yearsExperience": skill.get("years_experience") or skill.get("yearsExperience"),
    }


def map_avionte_skill_to_internal(skill: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Avionté skill format to internal skill format
    
    Args:
        skill: Avionté skill dictionary
        
    Returns:
        Internal skill dictionary
    """
    return {
        "name": skill.get("name", ""),
        "category": skill.get("category"),
        "years_experience": skill.get("yearsExperience"),
    }


def map_certification_to_avionte(cert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map internal certification format to Avionté certification format
    
    Args:
        cert: Internal certification dictionary
        
    Returns:
        Avionté certification dictionary
    """
    return {
        "name": cert.get("name", ""),
        "category": cert.get("category"),
        "issueDate": cert.get("issue_date") or cert.get("issueDate"),
        "expiryDate": cert.get("expiry_date") or cert.get("expiryDate"),
        "issuingOrganization": cert.get("issuing_organization") or cert.get("issuingOrganization"),
    }


def map_avionte_certification_to_internal(cert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Avionté certification format to internal certification format
    
    Args:
        cert: Avionté certification dictionary
        
    Returns:
        Internal certification dictionary
    """
    return {
        "name": cert.get("name", ""),
        "category": cert.get("category"),
        "issue_date": cert.get("issueDate"),
        "expiry_date": cert.get("expiryDate"),
        "issuing_organization": cert.get("issuingOrganization"),
    }
