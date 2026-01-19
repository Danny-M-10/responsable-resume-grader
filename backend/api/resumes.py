"""
Resumes API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy import text

from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.resume_service import parse_multiple_resumes_async
from backend.services.vault_service import save_asset_async
from storage import save_bytes

router = APIRouter()


async def check_duplicate_resume(
    file_hash: str,
    user_id: str,
    db: AsyncSession
) -> Optional[dict]:
    """
    Check if a resume with this file hash already exists for the user.

    Returns:
        Dict with existing candidate info if duplicate found, None otherwise
    """
    import os
    db_url = os.environ.get("DATABASE_URL", "")
    is_postgres = "postgres" in db_url.lower()

    if is_postgres:
        # PostgreSQL JSON syntax
        result = await db.execute(
            text("""
                SELECT fa.id as asset_id, fa.metadata_json, c.id as candidate_id, c.name, c.email, c.phone, c.parsed_data
                FROM file_assets fa
                LEFT JOIN candidates c ON c.id = (fa.metadata_json::json->>'candidate_id')
                WHERE fa.user_id = :user_id
                AND fa.kind = 'resume'
                AND fa.metadata_json::json->>'file_hash' = :file_hash
                LIMIT 1
            """),
            {"user_id": user_id, "file_hash": file_hash}
        )
    else:
        # SQLite JSON syntax
        result = await db.execute(
            text("""
                SELECT fa.id as asset_id, fa.metadata_json, c.id as candidate_id, c.name, c.email, c.phone, c.parsed_data
                FROM file_assets fa
                LEFT JOIN candidates c ON c.id = json_extract(fa.metadata_json, '$.candidate_id')
                WHERE fa.user_id = :user_id
                AND fa.kind = 'resume'
                AND json_extract(fa.metadata_json, '$.file_hash') = :file_hash
                LIMIT 1
            """),
            {"user_id": user_id, "file_hash": file_hash}
        )

    row = result.fetchone()

    if row:
        metadata = json.loads(row[1]) if row[1] else {}
        parsed_data = json.loads(row[6]) if row[6] else metadata
        return {
            "asset_id": row[0],
            "candidate_id": row[2] or metadata.get("candidate_id"),
            "name": row[3] or metadata.get("name", ""),
            "email": row[4] or metadata.get("email", ""),
            "phone": row[5] or metadata.get("phone", ""),
            "parsed_data": parsed_data
        }

    return None


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
    
    # Read all files and compute hashes for duplicate detection
    file_data = []
    file_hashes = []
    for file in files:
        content = await file.read()
        filename = file.filename or "resume.pdf"
        file_hash = hashlib.sha256(content).hexdigest()
        file_data.append((content, filename))
        file_hashes.append(file_hash)

    try:
        # Check for duplicates first
        total_files = len(file_data)
        candidate_ids = [None] * total_files
        asset_ids = [None] * total_files
        parsed_results = [None] * total_files
        duplicate_indices = []  # Track which files are duplicates
        duplicates_found = []  # Track duplicate info for response

        for i, file_hash in enumerate(file_hashes):
            existing = await check_duplicate_resume(file_hash, user_id, db)
            if existing and existing.get("candidate_id"):
                # This is a duplicate - use existing candidate
                candidate_ids[i] = existing["candidate_id"]
                asset_ids[i] = existing.get("asset_id") or ""
                parsed_results[i] = existing.get("parsed_data", {})
                duplicate_indices.append(i)
                duplicates_found.append({
                    "filename": file_data[i][1],
                    "candidate_id": existing["candidate_id"],
                    "name": existing.get("name", ""),
                    "is_duplicate": True
                })

        # Filter out duplicates for parsing
        new_indices = [i for i in range(len(file_data)) if i not in duplicate_indices]
        new_file_data = [file_data[i] for i in new_indices]
        new_file_hashes = [file_hashes[i] for i in new_indices]

        # Parse only new resumes
        if new_file_data:
            new_parsed_results = await parse_multiple_resumes_async(new_file_data, client_id)

            # Store new candidates in database and save to vault
            created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            for i, parsed_data in enumerate(new_parsed_results):
                original_index = new_indices[i]
                candidate_id = str(uuid.uuid4())
                candidate_ids[original_index] = candidate_id

                # Save resume file to persistent storage
                file_content, filename = new_file_data[i] if i < len(new_file_data) else (None, None)
                stored_path = None
                if file_content and filename:
                    stored_path, _ = save_bytes(file_content, filename)

                # Save to candidates table
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
                        "resume_path": stored_path,
                        "parsed_data": json.dumps(parsed_data),
                        "created_at": created_at,
                        "updated_at": created_at
                    }
                )

                # Also save to vault (file_assets table)
                if file_content and filename:
                    metadata = {
                        "source": "upload",
                        "candidate_id": candidate_id,
                        "name": parsed_data.get("name", ""),
                        "email": parsed_data.get("email", ""),
                        "phone": parsed_data.get("phone", ""),
                        "skills": parsed_data.get("skills", []),
                        "certifications": parsed_data.get("certifications", []),
                        "location": parsed_data.get("location", ""),
                        "years_of_experience": parsed_data.get("years_of_experience"),
                        "tags": [],
                        "file_hash": new_file_hashes[i]  # Store hash for future duplicate detection
                    }
                    asset_id = await save_asset_async(
                        user_id=user_id,
                        kind="resume",
                        original_name=filename,
                        content=file_content,
                        metadata=metadata,
                        db=db,
                        auto_commit=False
                    )
                    asset_ids[original_index] = asset_id

                parsed_results[original_index] = parsed_data

            # Commit all changes together
            await db.commit()

        # Build response message
        new_count = len(new_file_data)
        dup_count = len(duplicates_found)
        if dup_count > 0 and new_count > 0:
            message = f"Processed {new_count} new resume(s), {dup_count} duplicate(s) found (using existing)"
        elif dup_count > 0:
            message = f"All {dup_count} resume(s) already exist in the system (using existing)"
        else:
            message = f"Successfully parsed {new_count} resume(s)"

        return {
            "message": message,
            "candidate_ids": candidate_ids,
            "asset_ids": asset_ids,
            "parsed_data": parsed_results,
            "client_id": client_id,
            "duplicates": duplicates_found if duplicates_found else None
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
