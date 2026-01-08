"""
Candidates API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import text

from datetime import datetime
from backend.models.schemas import CandidateResponse
from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=List[CandidateResponse])
async def list_candidates(
    search: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List all candidates for current user with optional search
    
    Args:
        search: Optional search query
        user_id: Current user ID
        db: Database session
        
    Returns:
        List of candidates
    """
    if search:
        result = await db.execute(
            text("""
                SELECT id, user_id, name, email, phone, resume_path, parsed_data, created_at, updated_at
                FROM candidates
                WHERE user_id = :user_id
                AND (name ILIKE :search OR email ILIKE :search)
                ORDER BY created_at DESC
            """),
            {"user_id": user_id, "search": f"%{search}%"}
        )
    else:
        result = await db.execute(
            text("""
                SELECT id, user_id, name, email, phone, resume_path, parsed_data, created_at, updated_at
                FROM candidates
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": user_id}
        )
    
    rows = result.fetchall()
    
    return [
        CandidateResponse(
            id=row[0],
            user_id=row[1],
            name=row[2],
            email=row[3],
            phone=row[4],
            resume_path=row[5],
            parsed_data=None,  # TODO: Parse stored data
            created_at=datetime.fromisoformat(row[7].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row[8].replace("Z", "+00:00"))
        )
        for row in rows
    ]


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get candidate by ID
    
    Args:
        candidate_id: Candidate ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Candidate information
    """
    result = await db.execute(
        text("""
            SELECT id, user_id, name, email, phone, resume_path, parsed_data, created_at, updated_at
            FROM candidates
            WHERE id = :candidate_id AND user_id = :user_id
        """),
        {"candidate_id": candidate_id, "user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return CandidateResponse(
        id=row[0],
        user_id=row[1],
        name=row[2],
        email=row[3],
        phone=row[4],
        resume_path=row[5],
        parsed_data=None,
        created_at=datetime.fromisoformat(row[7].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row[8].replace("Z", "+00:00"))
    )
