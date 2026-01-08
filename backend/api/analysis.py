"""
Analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from datetime import datetime
from sqlalchemy import text

from backend.models.schemas import AnalysisConfig, AnalysisResponse
from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.analysis_service import run_analysis_async

router = APIRouter()


@router.post("/start", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    config: AnalysisConfig,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Start candidate analysis
    
    Args:
        config: Analysis configuration
        background_tasks: FastAPI background tasks
        user_id: Current user ID
        db: Database session
        
    Returns:
        Analysis information
    """
    # Create analysis record
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    client_id = str(uuid.uuid4())
    
    await db.execute(
        text("""
            INSERT INTO analyses (id, user_id, job_id, status, config, created_at, updated_at)
            VALUES (:id, :user_id, :job_id, :status, :config, :created_at, :updated_at)
        """),
        {
            "id": analysis_id,
            "user_id": user_id,
            "job_id": config.job_id,
            "status": "processing",
            "config": str(config.dict()),
            "created_at": created_at,
            "updated_at": created_at
        }
    )
    await db.commit()
    
    # Start background task
    background_tasks.add_task(
        run_analysis_async,
        config.job_id,
        config.candidate_ids,
        config.dict(),
        client_id
    )
    
    return AnalysisResponse(
        id=analysis_id,
        user_id=user_id,
        job_id=config.job_id,
        status="processing",
        results=None,
        created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis by ID
    
    Args:
        analysis_id: Analysis ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Analysis information
    """
    result = await db.execute(
        text("""
            SELECT id, user_id, job_id, status, results, created_at, updated_at
            FROM analyses
            WHERE id = :analysis_id AND user_id = :user_id
        """),
        {"analysis_id": analysis_id, "user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return AnalysisResponse(
        id=row[0],
        user_id=row[1],
        job_id=row[2],
        status=row[3],
        results=None,  # TODO: Parse stored results
        created_at=datetime.fromisoformat(row[5].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row[6].replace("Z", "+00:00"))
    )


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List all analyses for current user
    
    Args:
        user_id: Current user ID
        db: Database session
        
    Returns:
        List of analyses
    """
    result = await db.execute(
        text("""
            SELECT id, user_id, job_id, status, results, created_at, updated_at
            FROM analyses
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """),
        {"user_id": user_id}
    )
    rows = result.fetchall()
    
    return [
        AnalysisResponse(
            id=row[0],
            user_id=row[1],
            job_id=row[2],
            status=row[3],
            results=None,
            created_at=datetime.fromisoformat(row[5].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row[6].replace("Z", "+00:00"))
        )
        for row in rows
    ]
