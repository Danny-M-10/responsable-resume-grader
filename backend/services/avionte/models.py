"""
Pydantic models for Avionté API data structures
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Common Models
class AvionteAddress(BaseModel):
    """Address model"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None


class AvionteContact(BaseModel):
    """Contact information model"""
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None


# Talent Models
class AvionteCertification(BaseModel):
    """Certification model"""
    certificationId: Optional[str] = None
    name: str
    category: Optional[str] = None
    issueDate: Optional[datetime] = None
    expiryDate: Optional[datetime] = None
    issuingOrganization: Optional[str] = None


class AvionteSkill(BaseModel):
    """Skill model"""
    skillId: Optional[str] = None
    name: str
    category: Optional[str] = None
    yearsExperience: Optional[int] = None


class AvionteWorkHistory(BaseModel):
    """Work history model"""
    workHistoryId: Optional[str] = None
    companyName: str
    jobTitle: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    description: Optional[str] = None
    isCurrent: Optional[bool] = False


class AvionteEducation(BaseModel):
    """Education model"""
    educationId: Optional[str] = None
    institution: str
    degree: Optional[str] = None
    fieldOfStudy: Optional[str] = None
    graduationDate: Optional[datetime] = None
    gpa: Optional[float] = None


class AvionteTalent(BaseModel):
    """Talent (candidate) model"""
    talentId: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[AvionteAddress] = None
    skills: Optional[List[AvionteSkill]] = []
    certifications: Optional[List[AvionteCertification]] = []
    workHistory: Optional[List[AvionteWorkHistory]] = []
    education: Optional[List[AvionteEducation]] = []
    resume: Optional[str] = None  # Base64 encoded or URL
    status: Optional[str] = None
    tags: Optional[List[str]] = []
    customFields: Optional[Dict[str, Any]] = {}


# Job Models
class AvionteJobSkill(BaseModel):
    """Job skill requirement"""
    skillId: Optional[str] = None
    name: str
    required: bool = True
    yearsExperience: Optional[int] = None


class AvionteJobCertification(BaseModel):
    """Job certification requirement"""
    certificationId: Optional[str] = None
    name: str
    required: bool = True


class AvionteJob(BaseModel):
    """Job model"""
    jobId: Optional[str] = None
    jobTitle: str
    description: Optional[str] = None
    location: Optional[str] = None
    address: Optional[AvionteAddress] = None
    requiredSkills: Optional[List[AvionteJobSkill]] = []
    requiredCertifications: Optional[List[AvionteJobCertification]] = []
    employmentType: Optional[str] = None
    status: Optional[str] = None
    companyId: Optional[str] = None
    branchId: Optional[str] = None
    customFields: Optional[Dict[str, Any]] = {}


# Company Models
class AvionteCompany(BaseModel):
    """Company model"""
    companyId: Optional[str] = None
    companyName: str
    address: Optional[AvionteAddress] = None
    contact: Optional[AvionteContact] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = []
    customFields: Optional[Dict[str, Any]] = {}


# Placement Models
class AviontePlacement(BaseModel):
    """Placement model"""
    placementId: Optional[str] = None
    talentId: str
    jobId: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    payRate: Optional[float] = None
    customFields: Optional[Dict[str, Any]] = {}


# Query/Response Models
class AvionteQueryRequest(BaseModel):
    """Query request model"""
    filters: Optional[Dict[str, Any]] = {}
    page: Optional[int] = 1
    pageSize: Optional[int] = 50
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = "asc"


class AvionteQueryResponse(BaseModel):
    """Query response model"""
    data: List[Dict[str, Any]]
    total: Optional[int] = None
    page: Optional[int] = None
    pageSize: Optional[int] = None
    totalPages: Optional[int] = None


# Document Models
class AvionteDocument(BaseModel):
    """Document model"""
    documentId: Optional[str] = None
    fileName: str
    fileType: Optional[str] = None
    fileSize: Optional[int] = None
    uploadDate: Optional[datetime] = None
    documentType: Optional[str] = None
    url: Optional[str] = None
