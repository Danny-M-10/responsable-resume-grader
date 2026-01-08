"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Authentication schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Job schemas
class JobUpload(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class JobParsed(BaseModel):
    job_title: str
    location: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: str
    certifications: List[Dict[str, str]]
    industry_context: Optional[str] = None
    soft_skills: Optional[List[str]] = None
    technical_stack: Optional[List[str]] = None


class JobResponse(BaseModel):
    id: str
    user_id: str
    title: str
    location: str
    parsed_data: Optional[JobParsed] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Resume/Candidate schemas
class ResumeUpload(BaseModel):
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None


class CandidateResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Analysis schemas
class AnalysisConfig(BaseModel):
    job_id: str
    candidate_ids: List[str]
    industry_template: Optional[str] = "general"
    custom_scoring_weights: Optional[Dict[str, float]] = None
    dealbreakers: Optional[List[str]] = None
    bias_reduction_enabled: bool = False


class AnalysisResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    status: str  # pending, processing, completed, failed
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Report schemas
class ReportResponse(BaseModel):
    id: str
    analysis_id: str
    pdf_path: str
    created_at: datetime

    class Config:
        from_attributes = True


# Progress schemas
class ProgressUpdate(BaseModel):
    step: str
    progress: float  # 0.0 to 1.0
    current: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None


# Vault schemas
class AssetResponse(BaseModel):
    id: str
    original_name: str
    stored_path: str
    metadata: Dict[str, Any]
    created_at: str
    
    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]

