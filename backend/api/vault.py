"""
Vault API endpoints for managing saved job descriptions and resumes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import logging

from backend.models.schemas import AssetResponse, AssetListResponse
from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.vault_service import (
    save_asset_async,
    list_assets_async,
    get_asset_async,
    delete_asset_async,
    load_asset_content
)
from backend.services.resume_service import parse_resume_file_async
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateTagsRequest(BaseModel):
    tags: List[str]


@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def save_asset(
    file: UploadFile = File(...),
    kind: str = Query(..., regex="^(job_description|resume)$", description="Asset kind: job_description or resume"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Save asset to vault
    
    Args:
        file: File to save (PDF, DOCX, or TXT)
        kind: Asset kind ('job_description' or 'resume')
        user_id: Current user ID
        db: Database session
        
    Returns:
        Asset information
    """
    # Read file content
    content = await file.read()
    filename = file.filename or "file"
    
    try:
        # Parse resume if it's a resume file
        metadata = {"source": "vault"}
        if kind == "resume":
            try:
                parsed_data = await parse_resume_file_async(content, filename, client_id="vault_save")
                # Extract key fields from parsed data to store in metadata
                if parsed_data:
                    metadata["name"] = parsed_data.get("name", "")
                    metadata["email"] = parsed_data.get("email", "")
                    metadata["phone"] = parsed_data.get("phone", "")
                    metadata["skills"] = parsed_data.get("skills", [])
                    metadata["certifications"] = parsed_data.get("certifications", [])
                    metadata["location"] = parsed_data.get("location", "")
                    metadata["years_of_experience"] = parsed_data.get("years_of_experience")
                    # Initialize tags array if not present
                    metadata.setdefault("tags", [])
            except Exception as parse_error:
                # Log parsing error but don't fail the save
                logger.warning(f"Failed to parse resume {filename}: {parse_error}", exc_info=True)
                # Save with minimal metadata (source and file_hash will be added)
        
        # Save asset without auto-commit; commit after successful retrieval
        asset_id = await save_asset_async(
            user_id=user_id,
            kind=kind,
            original_name=filename,
            content=content,
            metadata=metadata,
            db=db,
            auto_commit=False
        )
        
        # Get saved asset
        asset = await get_asset_async(asset_id, db)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve saved asset"
            )

        await db.commit()
        
        return AssetResponse(
            id=asset["id"],
            original_name=asset["original_name"],
            stored_path=asset["stored_path"],
            metadata=asset["metadata"],
            created_at=asset["created_at"]
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save asset: {str(e)}"
        )


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    kind: str = Query(..., regex="^(job_description|resume)$", description="Asset kind: job_description or resume"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills to filter by"),
    name: Optional[str] = Query(None, description="Filter by candidate name (partial match)"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List assets for current user by kind with optional filters
    
    Args:
        kind: Asset kind ('job_description' or 'resume')
        search: Full-text search query
        tags: Comma-separated list of tags to filter by
        skills: Comma-separated list of skills to filter by
        name: Filter by candidate name (partial match)
        user_id: Current user ID
        db: Database session
        
    Returns:
        List of assets
    """
    try:
        # Parse comma-separated tag and skill filters, stripping whitespace and removing empties
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else None
        skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()] if skills else None
        
        assets = await list_assets_async(
            user_id, 
            kind, 
            db,
            search=search,
            tags=tag_list,
            skills=skill_list,
            name=name
        )
        
        return AssetListResponse(
            assets=[
                AssetResponse(
                    id=asset["id"],
                    original_name=asset["original_name"],
                    stored_path=asset["stored_path"],
                    metadata=asset["metadata"],
                    created_at=asset["created_at"]
                )
                for asset in assets
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assets: {str(e)}"
        )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get asset by ID (only if owned by user)
    
    Args:
        asset_id: Asset ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Asset information
    """
    asset = await get_asset_async(asset_id, db)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Check ownership
    if asset["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return AssetResponse(
        id=asset["id"],
        original_name=asset["original_name"],
        stored_path=asset["stored_path"],
        metadata=asset["metadata"],
        created_at=asset["created_at"]
    )


@router.get("/assets/{asset_id}/download")
async def download_asset(
    asset_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Download asset file content
    
    Args:
        asset_id: Asset ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        File content
    """
    asset = await get_asset_async(asset_id, db)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Check ownership
    if asset["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Load file content
    content = load_asset_content(asset)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    # Determine content type
    filename = asset["original_name"]
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif filename.endswith(".txt"):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.put("/assets/{asset_id}/tags", response_model=AssetResponse)
async def update_asset_tags(
    asset_id: str,
    request: UpdateTagsRequest = Body(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update tags for an asset
    
    Args:
        asset_id: Asset ID
        request: Request body with tags list
        user_id: Current user ID
        db: Database session
        
    Returns:
        Updated asset information
    """
    from backend.services.vault_service import update_asset_tags_async
    
    asset = await update_asset_tags_async(asset_id, request.tags, user_id, db)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found or access denied"
        )
    
    return AssetResponse(
        id=asset["id"],
        original_name=asset["original_name"],
        stored_path=asset["stored_path"],
        metadata=asset["metadata"],
        created_at=asset["created_at"]
    )


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete asset (only if owned by user)
    
    Args:
        asset_id: Asset ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        204 No Content if successful
    """
    deleted = await delete_asset_async(asset_id, user_id, db)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found or access denied"
        )
    
    return None
