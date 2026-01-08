"""
Vault API endpoints for managing saved job descriptions and resumes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

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
from fastapi.responses import Response

router = APIRouter()


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
        # Save asset
        asset_id = await save_asset_async(
            user_id=user_id,
            kind=kind,
            original_name=filename,
            content=content,
            metadata={"source": "vault"},
            db=db
        )
        
        # Get saved asset
        asset = await get_asset_async(asset_id, db)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve saved asset"
            )
        
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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List assets for current user by kind
    
    Args:
        kind: Asset kind ('job_description' or 'resume')
        user_id: Current user ID
        db: Database session
        
    Returns:
        List of assets
    """
    try:
        assets = await list_assets_async(user_id, kind, db)
        
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
