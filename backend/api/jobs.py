"""
Jobs API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import text

from backend.models.schemas import JobResponse, JobParsed, JobUpload
from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.job_service import parse_job_file_async

router = APIRouter()


@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def upload_job(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and parse job description file
    
    Args:
        file: Job description file (PDF, DOCX, or TXT)
        user_id: Current user ID
        db: Database session
        
    Returns:
        Job information with parsed data
    """
    # Read file content
    file_content = await file.read()
    filename = file.filename or "job_description.txt"
    
    # Generate client ID for WebSocket progress
    client_id = str(uuid.uuid4())
    
    try:
        # Parse job file
        parsed_data = await parse_job_file_async(file_content, filename, client_id)
        
        # Store job in database
        job_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        
        await db.execute(
            text("""
                INSERT INTO jobs (id, user_id, title, location, parsed_data, created_at, updated_at)
                VALUES (:id, :user_id, :title, :location, :parsed_data, :created_at, :updated_at)
            """),
            {
                "id": job_id,
                "user_id": user_id,
                "title": parsed_data.get("job_title", ""),
                "location": parsed_data.get("location", ""),
                "parsed_data": str(parsed_data),  # Store as string for now
                "created_at": created_at,
                "updated_at": created_at
            }
        )
        await db.commit()
        
        return JobResponse(
            id=job_id,
            user_id=user_id,
            title=parsed_data.get("job_title", ""),
            location=parsed_data.get("location", ""),
            parsed_data=JobParsed(**parsed_data) if parsed_data else None,
            created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse job description: {str(e)}"
        )


@router.post("/create", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job_manual(
    job_data: JobUpload,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create job manually (without file upload)
    
    Args:
        job_data: Job information
        user_id: Current user ID
        db: Database session
        
    Returns:
        Job information
    """
    if not job_data.title or not job_data.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job title and description are required"
        )
    
    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    
    # Create a minimal parsed_data structure
    parsed_data = {
        "job_title": job_data.title,
        "location": job_data.location or "",
        "full_description": job_data.description,
        "required_skills": [],
        "preferred_skills": [],
        "experience_level": "",
        "certifications": [],
    }
    
    try:
        await db.execute(
            text("""
                INSERT INTO jobs (id, user_id, title, location, parsed_data, created_at, updated_at)
                VALUES (:id, :user_id, :title, :location, :parsed_data, :created_at, :updated_at)
            """),
            {
                "id": job_id,
                "user_id": user_id,
                "title": job_data.title,
                "location": job_data.location or "",
                "parsed_data": str(parsed_data),
                "created_at": created_at,
                "updated_at": created_at
            }
        )
        await db.commit()
        
        return JobResponse(
            id=job_id,
            user_id=user_id,
            title=job_data.title,
            location=job_data.location or "",
            parsed_data=JobParsed(**parsed_data),
            created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job by ID
    
    Args:
        job_id: Job ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Job information
    """
    result = await db.execute(
        text("SELECT id, user_id, title, location, parsed_data, created_at, updated_at FROM jobs WHERE id = :job_id AND user_id = :user_id"),
        {"job_id": job_id, "user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobResponse(
        id=row[0],
        user_id=row[1],
        title=row[2],
        location=row[3],
        parsed_data=None,  # TODO: Parse stored data
        created_at=datetime.fromisoformat(row[5].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row[6].replace("Z", "+00:00"))
    )


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List all jobs for current user
    
    Args:
        user_id: Current user ID
        db: Database session
        
    Returns:
        List of jobs
    """
    result = await db.execute(
        text("SELECT id, user_id, title, location, parsed_data, created_at, updated_at FROM jobs WHERE user_id = :user_id ORDER BY created_at DESC"),
        {"user_id": user_id}
    )
    rows = result.fetchall()
    
    return [
        JobResponse(
            id=row[0],
            user_id=row[1],
            title=row[2],
            location=row[3],
            parsed_data=None,
            created_at=datetime.fromisoformat(row[5].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row[6].replace("Z", "+00:00"))
        )
        for row in rows
    ]
