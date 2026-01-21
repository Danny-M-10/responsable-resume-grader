"""
Data transformation functions between internal models and Avionté models
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .models import (
    AvionteTalent,
    AvionteJob,
    AvionteSkill,
    AvionteCertification,
    AvionteWorkHistory,
    AvionteEducation,
    AvionteAddress,
)
from .mappers import (
    map_talent_name_to_avionte,
    map_avionte_name_to_internal,
    map_skill_to_avionte,
    map_avionte_skill_to_internal,
    map_certification_to_avionte,
    map_avionte_certification_to_internal,
)

logger = logging.getLogger(__name__)


def transform_candidate_to_avionte_talent(candidate: Dict[str, Any]) -> AvionteTalent:
    """
    Transform internal candidate profile to Avionté Talent model
    
    Args:
        candidate: Internal candidate dictionary
        
    Returns:
        Avionté Talent model
    """
    # Handle name splitting
    name = candidate.get("name", "")
    name_parts = map_talent_name_to_avionte(name)
    
    # Transform skills
    skills = []
    for skill in candidate.get("skills", []):
        avionte_skill = map_skill_to_avionte(skill)
        skills.append(AvionteSkill(**avionte_skill))
    
    # Transform certifications
    certifications = []
    for cert in candidate.get("certifications", []):
        avionte_cert = map_certification_to_avionte(cert)
        certifications.append(AvionteCertification(**avionte_cert))
    
    # Transform work history
    work_history = []
    for work in candidate.get("work_history", []):
        work_history.append(AvionteWorkHistory(
            companyName=work.get("company", ""),
            jobTitle=work.get("title", ""),
            startDate=work.get("start_date"),
            endDate=work.get("end_date"),
            description=work.get("description"),
            isCurrent=work.get("is_current", False)
        ))
    
    # Transform education
    education = []
    for edu in candidate.get("education", []):
        education.append(AvionteEducation(
            institution=edu.get("institution", ""),
            degree=edu.get("degree"),
            fieldOfStudy=edu.get("field_of_study") or edu.get("fieldOfStudy"),
            graduationDate=edu.get("graduation_date") or edu.get("graduationDate"),
            gpa=edu.get("gpa")
        ))
    
    # Build talent model
    talent = AvionteTalent(
        talentId=candidate.get("avionte_talent_id"),
        firstName=name_parts.get("firstName"),
        lastName=name_parts.get("lastName"),
        email=candidate.get("email"),
        phone=candidate.get("phone"),
        mobile=candidate.get("mobile"),
        skills=skills if skills else None,
        certifications=certifications if certifications else None,
        workHistory=work_history if work_history else None,
        education=education if education else None,
        status=candidate.get("status"),
        tags=candidate.get("tags", []),
    )
    
    return talent


def transform_avionte_talent_to_candidate(talent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Avionté Talent data to internal candidate profile
    
    Args:
        talent_data: Avionté Talent dictionary
        
    Returns:
        Internal candidate dictionary
    """
    # Combine name
    name = map_avionte_name_to_internal(
        talent_data.get("firstName"),
        talent_data.get("lastName")
    )
    
    # Transform skills
    skills = []
    for skill in talent_data.get("skills", []):
        internal_skill = map_avionte_skill_to_internal(skill)
        skills.append(internal_skill)
    
    # Transform certifications
    certifications = []
    for cert in talent_data.get("certifications", []):
        internal_cert = map_avionte_certification_to_internal(cert)
        certifications.append(internal_cert)
    
    # Transform work history
    work_history = []
    for work in talent_data.get("workHistory", []):
        work_history.append({
            "company": work.get("companyName", ""),
            "title": work.get("jobTitle", ""),
            "start_date": work.get("startDate"),
            "end_date": work.get("endDate"),
            "description": work.get("description"),
            "is_current": work.get("isCurrent", False)
        })
    
    # Transform education
    education = []
    for edu in talent_data.get("education", []):
        education.append({
            "institution": edu.get("institution", ""),
            "degree": edu.get("degree"),
            "field_of_study": edu.get("fieldOfStudy"),
            "graduation_date": edu.get("graduationDate"),
            "gpa": edu.get("gpa")
        })
    
    # Build candidate dictionary
    candidate = {
        "avionte_talent_id": talent_data.get("talentId"),
        "name": name,
        "email": talent_data.get("email"),
        "phone": talent_data.get("phone"),
        "mobile": talent_data.get("mobile"),
        "skills": skills,
        "certifications": certifications,
        "work_history": work_history,
        "education": education,
        "status": talent_data.get("status"),
        "tags": talent_data.get("tags", []),
    }
    
    return candidate


def transform_job_to_avionte_job(job: Dict[str, Any]) -> AvionteJob:
    """
    Transform internal job description to Avionté Job model
    
    Args:
        job: Internal job dictionary
        
    Returns:
        Avionté Job model
    """
    from .models import AvionteJobSkill, AvionteJobCertification
    
    # Transform required skills
    required_skills = []
    for skill in job.get("required_skills", []):
        required_skills.append(AvionteJobSkill(
            name=skill.get("name", ""),
            required=True,
            yearsExperience=skill.get("years_experience") or skill.get("yearsExperience")
        ))
    
    # Transform certifications
    required_certifications = []
    for cert in job.get("certifications", []):
        cert_name = cert if isinstance(cert, str) else cert.get("name", "")
        required_certifications.append(AvionteJobCertification(
            name=cert_name,
            required=cert.get("category") == "must-have" if isinstance(cert, dict) else True
        ))
    
    # Build job model
    avionte_job = AvionteJob(
        jobId=job.get("avionte_job_id"),
        jobTitle=job.get("title", ""),
        description=job.get("full_description") or job.get("description", ""),
        location=job.get("location"),
        requiredSkills=required_skills if required_skills else None,
        requiredCertifications=required_certifications if required_certifications else None,
        employmentType=job.get("employment_type"),
        status=job.get("status"),
        companyId=job.get("company_id"),
        branchId=job.get("branch_id"),
    )
    
    return avionte_job


def transform_avionte_job_to_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Avionté Job data to internal job description
    
    Args:
        job_data: Avionté Job dictionary
        
    Returns:
        Internal job dictionary
    """
    # Transform required skills
    required_skills = []
    for skill in job_data.get("requiredSkills", []):
        required_skills.append({
            "name": skill.get("name", ""),
            "years_experience": skill.get("yearsExperience")
        })
    
    # Transform certifications
    certifications = []
    for cert in job_data.get("requiredCertifications", []):
        cert_name = cert if isinstance(cert, str) else cert.get("name", "")
        certifications.append({
            "name": cert_name,
            "category": "must-have" if cert.get("required", True) else "bonus"
        })
    
    # Build job dictionary
    job = {
        "avionte_job_id": job_data.get("jobId"),
        "title": job_data.get("jobTitle", ""),
        "description": job_data.get("description", ""),
        "full_description": job_data.get("description", ""),
        "location": job_data.get("location"),
        "required_skills": required_skills,
        "certifications": certifications,
        "employment_type": job_data.get("employmentType"),
        "status": job_data.get("status"),
        "company_id": job_data.get("companyId"),
        "branch_id": job_data.get("branchId"),
    }
    
    return job
