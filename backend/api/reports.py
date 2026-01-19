"""
Reports API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import json
import os

from backend.models.schemas import ReportResponse
from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from pdf_generator import PDFGenerator
from models import JobDetails, CandidateScore, Certification

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
    from datetime import datetime, timezone
    import uuid

    # Load analysis from database
    analysis_result = await db.execute(
        text("""
            SELECT a.id, a.job_id, a.status, a.results, j.title, j.location, j.parsed_data
            FROM analyses a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.id = :analysis_id AND a.user_id = :user_id
        """),
        {"analysis_id": analysis_id, "user_id": user_id}
    )
    analysis_row = analysis_result.fetchone()

    if not analysis_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    analysis_status = analysis_row[2]
    results_str = analysis_row[3]
    job_title = analysis_row[4]
    job_location = analysis_row[5]
    job_parsed_data_str = analysis_row[6]

    if analysis_status != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed (status: {analysis_status})"
        )

    # Parse results JSON
    try:
        results = json.loads(results_str) if results_str else {}
    except json.JSONDecodeError:
        results = {}

    # Import storage utilities
    import tempfile
    from storage import save_bytes, load_bytes

    # Generate report ID upfront
    report_id = str(uuid.uuid4())

    # Check if PDF already exists from analysis (handle both S3 and local paths)
    existing_pdf_path = results.get("pdf_path")
    pdf_exists = False
    if existing_pdf_path:
        if existing_pdf_path.startswith("s3://"):
            # Check S3 by trying to load (will return None if not found)
            pdf_exists = load_bytes(existing_pdf_path) is not None
        else:
            pdf_exists = os.path.exists(existing_pdf_path)

    if pdf_exists:
        pdf_path = existing_pdf_path
    else:
        # Generate new PDF report
        # Parse job data
        try:
            job_parsed_data = json.loads(job_parsed_data_str) if job_parsed_data_str else {}
        except json.JSONDecodeError:
            job_parsed_data = {}

        # Build JobDetails object
        certifications = []
        for cert in job_parsed_data.get("certifications", []):
            if isinstance(cert, dict):
                certifications.append(Certification(
                    name=cert.get("name", ""),
                    category=cert.get("category", "bonus")
                ))
            elif isinstance(cert, str):
                certifications.append(Certification(name=cert, category="bonus"))

        job_details = JobDetails(
            job_title=job_title or job_parsed_data.get("job_title", "Unknown"),
            location=job_location or job_parsed_data.get("location", ""),
            full_description=job_parsed_data.get("full_description", ""),
            required_skills=job_parsed_data.get("required_skills", []),
            preferred_skills=job_parsed_data.get("preferred_skills", []),
            experience_level=job_parsed_data.get("experience_level", ""),
            certifications=certifications,
            equivalent_titles=job_parsed_data.get("equivalent_titles", []),
            industry_template=job_parsed_data.get("industry_template", "general"),
            certification_equivalents=job_parsed_data.get("certification_equivalents", {})
        )

        # Build CandidateScore objects from results
        candidate_scores = []
        candidates_data = results.get("candidates", [])
        for candidate in candidates_data:
            candidate_scores.append(CandidateScore(
                name=candidate.get("name", "Unknown"),
                phone=candidate.get("phone", ""),
                email=candidate.get("email", ""),
                certifications=candidate.get("certifications", []),
                fit_score=candidate.get("fit_score", 0.0),
                chain_of_thought=candidate.get("chain_of_thought", ""),
                rationale=candidate.get("rationale", ""),
                experience_match=candidate.get("experience_match", {}),
                certification_match=candidate.get("certification_match", {}),
                skills_match=candidate.get("skills_match", {}),
                location_match=candidate.get("location_match", False),
                transferrable_skills_match=candidate.get("transferrable_skills_match", {}),
                component_scores=candidate.get("component_scores", {}),
                calibration_applied=candidate.get("calibration_applied", False),
                calibration_factor=candidate.get("calibration_factor", 1.0)
            ))

        # Sort candidates by score (highest first)
        candidate_scores.sort(key=lambda x: x.fit_score, reverse=True)

        # Generate PDF to temp file first, then upload to S3
        # Generate to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            temp_pdf_path = tmp_file.name

        pdf_generator = PDFGenerator()
        pdf_generator.generate(
            job_details=job_details,
            top_candidates=candidate_scores,
            all_candidates_count=len(candidate_scores),
            output_path=temp_pdf_path
        )

        # Read the generated PDF and save to S3
        with open(temp_pdf_path, "rb") as f:
            pdf_content = f.read()

        # Save to S3 (or local storage fallback)
        pdf_path, _ = save_bytes(pdf_content, f"report_{report_id}.pdf")

        # Clean up temp file
        os.unlink(temp_pdf_path)

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Store report in database
    await db.execute(
        text("""
            INSERT INTO reports (id, analysis_id, user_id, pdf_path, created_at)
            VALUES (:id, :analysis_id, :user_id, :pdf_path, :created_at)
        """),
        {
            "id": report_id,
            "analysis_id": analysis_id,
            "user_id": user_id,
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
    Download PDF report (supports both S3 and local storage)

    Args:
        report_id: Report ID
        user_id: Current user ID
        db: Database session

    Returns:
        PDF file
    """
    from fastapi.responses import StreamingResponse
    from storage import load_bytes
    import io

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

    # Handle S3 paths
    if pdf_path and pdf_path.startswith("s3://"):
        content = load_bytes(pdf_path)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found in S3"
            )
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=candidate_report_{report_id}.pdf"}
        )

    # Handle local paths
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
