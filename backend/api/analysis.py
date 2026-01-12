"""
Analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import json
from datetime import datetime
from sqlalchemy import text
from pathlib import Path

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
    # Use client_id from request if provided, otherwise generate one
    client_id = config.client_id if config.client_id else str(uuid.uuid4())
    
    await db.execute(
        text("""
            INSERT INTO analyses (id, user_id, job_id, status, config, client_id, created_at, updated_at)
            VALUES (:id, :user_id, :job_id, :status, :config, :client_id, :created_at, :updated_at)
        """),
        {
            "id": analysis_id,
            "user_id": user_id,
            "job_id": config.job_id,
            "status": "processing",
            "config": json.dumps(config.dict()),  # Store as JSON string
            "client_id": client_id,
            "created_at": created_at,
            "updated_at": created_at
        }
    )
    await db.commit()
    
    # Start background task (pass analysis_id and user_id)
    background_tasks.add_task(
        run_analysis_async,
        analysis_id,
        config.job_id,
        config.candidate_ids,
        config.dict(),
        client_id,
        user_id
    )
    
    return AnalysisResponse(
        id=analysis_id,
        user_id=user_id,
        job_id=config.job_id,
        status="processing",
        results=None,
        created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
        client_id=client_id  # Return client_id so frontend knows which one to listen on
    )


# IMPORTANT: Empty string routes must come BEFORE path parameter routes
# to ensure /api/analysis matches this route instead of /{analysis_id}
@router.get("", response_model=List[AnalysisResponse], include_in_schema=True)
@router.get("/", response_model=List[AnalysisResponse], include_in_schema=True)
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
            SELECT id, user_id, job_id, status, results, client_id, created_at, updated_at
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
            client_id=row[5],  # client_id column (index 5)
            created_at=datetime.fromisoformat(row[6].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row[7].replace("Z", "+00:00"))
        )
        for row in rows
    ]


@router.get("/{analysis_id}/download-pdf")
async def download_analysis_pdf(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Download PDF report for analysis
    
    Args:
        analysis_id: Analysis ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        PDF file
    """
    result = await db.execute(
        text("""
            SELECT results
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
    
    # Parse results JSON to get PDF path
    results_data = None
    if row[0]:
        try:
            if isinstance(row[0], str):
                results_data = json.loads(row[0])
            else:
                results_data = row[0]
        except (json.JSONDecodeError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse analysis results for PDF download {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse analysis results"
            )
    
    if not results_data or "pdf_path" not in results_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report not found for this analysis"
        )
    
    pdf_path = results_data["pdf_path"]
    
    if not Path(pdf_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on server"
        )
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"candidate_report_{analysis_id}.pdf"
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
            SELECT id, user_id, job_id, status, results, client_id, created_at, updated_at
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
    
    # Parse results from database (stored as JSON string)
    results_data = None
    if row[4]:  # results column (index 4)
        try:
            if isinstance(row[4], str):
                results_data = json.loads(row[4])
            else:
                # If already a dict/list, use as-is
                results_data = row[4]
        except (json.JSONDecodeError, TypeError) as e:
            # If parsing fails, log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to parse analysis results for {analysis_id}: {e}")
            results_data = None
    
    return AnalysisResponse(
        id=row[0],
        user_id=row[1],
        job_id=row[2],
        status=row[3],
        results=results_data,  # Return parsed results from database
        client_id=row[5],  # client_id column (index 5)
        created_at=datetime.fromisoformat(row[6].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row[7].replace("Z", "+00:00"))
    )
