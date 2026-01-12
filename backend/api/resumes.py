"""
Resumes API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import json
from datetime import datetime
from sqlalchemy import text

from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.resume_service import parse_multiple_resumes_async
from storage import save_bytes

router = APIRouter()


@router.post("/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    client_id: Optional[str] = Query(None, description="Client ID for WebSocket progress updates"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and parse multiple resume files
    
    Args:
        files: List of resume files
        client_id: Optional client ID for WebSocket progress updates (if not provided, generates one)
        user_id: Current user ID
        db: Database session
        
    Returns:
        List of parsed candidate data with client_id
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Use provided client_id or generate one for WebSocket progress
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Read all files
    file_data = []
    for file in files:
        content = await file.read()
        filename = file.filename or "resume.pdf"
        file_data.append((content, filename))
    
    try:
        # Parse all resumes
        parsed_results = await parse_multiple_resumes_async(file_data, client_id)
        
        # Store candidates in database
        candidate_ids = []
        created_at = datetime.utcnow().isoformat() + "Z"
        
        for i, parsed_data in enumerate(parsed_results):
            candidate_id = str(uuid.uuid4())
            candidate_ids.append(candidate_id)
            
            # Save resume file to persistent storage
            file_content, filename = file_data[i] if i < len(file_data) else (None, None)
            stored_path = None
            if file_content and filename:
                stored_path, _ = save_bytes(file_content, filename)
            
            await db.execute(
                text("""
                    INSERT INTO candidates (id, user_id, name, email, phone, resume_path, parsed_data, created_at, updated_at)
                    VALUES (:id, :user_id, :name, :email, :phone, :resume_path, :parsed_data, :created_at, :updated_at)
                """),
                {
                    "id": candidate_id,
                    "user_id": user_id,
                    "name": parsed_data.get("name", ""),
                    "email": parsed_data.get("email", ""),
                    "phone": parsed_data.get("phone", ""),
                    "resume_path": stored_path,  # Store full path to saved file
                    "parsed_data": json.dumps(parsed_data),  # Store as JSON string
                    "created_at": created_at,
                    "updated_at": created_at
                }
            )
        
        await db.commit()
        
        return {
            "message": f"Successfully parsed {len(parsed_results)} resumes",
            "candidate_ids": candidate_ids,
            "parsed_data": parsed_results,
            "client_id": client_id  # Return client_id so frontend knows which one to listen on
        }
    except Exception as e:
        await db.rollback()
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_traceback = traceback.format_exc()
        logger.error(f"Failed to parse resumes: {str(e)}\nTraceback:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resumes: {str(e)}"
        )
