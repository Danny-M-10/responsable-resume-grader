"""
Reports API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path

from backend.models.schemas import ReportResponse
from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from pdf_generator import PDFGenerator

router = APIRouter()


@router.post("/generate/{analysis_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate PDF report for analysis
    
    Args:
        analysis_id: Analysis ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Report information
    """
    # TODO: Load analysis and generate PDF
    # For now, return placeholder
    from datetime import datetime
    import uuid
    
    report_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    
    # TODO: Actually generate PDF using PDFGenerator
    pdf_path = f"/tmp/report_{report_id}.pdf"
    
    await db.execute(
        text("""
            INSERT INTO reports (id, analysis_id, pdf_path, created_at)
            VALUES (:id, :analysis_id, :pdf_path, :created_at)
        """),
        {
            "id": report_id,
            "analysis_id": analysis_id,
            "pdf_path": pdf_path,
            "created_at": created_at
        }
    )
    await db.commit()
    
    return ReportResponse(
        id=report_id,
        analysis_id=analysis_id,
        pdf_path=pdf_path,
        created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Download PDF report
    
    Args:
        report_id: Report ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        PDF file
    """
    result = await db.execute(
        text("""
            SELECT r.pdf_path, a.user_id
            FROM reports r
            JOIN analyses a ON r.analysis_id = a.id
            WHERE r.id = :report_id AND a.user_id = :user_id
        """),
        {"report_id": report_id, "user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    pdf_path = row[0]
    
    if not Path(pdf_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"candidate_report_{report_id}.pdf"
    )
