"""
Async vault service for managing file assets
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from storage import save_bytes

logger = logging.getLogger(__name__)


def _safe_json_loads(json_str: str) -> Dict[str, Any]:
    """Safely parse JSON string"""
    if not json_str:
        return {}
    try:
        return json.loads(json_str)
    except:
        return {}


async def save_asset_async(
    user_id: str,
    kind: str,
    original_name: str,
    content: bytes,
    metadata: Dict[str, Any] = None,
    db: AsyncSession = None
) -> str:
    """
    Save asset to vault asynchronously
    
    Args:
        user_id: User ID
        kind: Asset kind ('job_description' or 'resume')
        original_name: Original filename
        content: File content as bytes
        metadata: Optional metadata dictionary
        db: Database session
        
    Returns:
        Asset ID
    """
    stored_path, file_hash = save_bytes(content, original_name)
    asset_id = str(uuid.uuid4())
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    
    metadata_dict = metadata or {}
    metadata_dict["file_hash"] = file_hash
    
    await db.execute(
        text("""
            INSERT INTO file_assets (id, user_id, kind, original_name, stored_path, metadata_json, created_at)
            VALUES (:id, :user_id, :kind, :original_name, :stored_path, :metadata_json, :created_at)
        """),
        {
            "id": asset_id,
            "user_id": user_id,
            "kind": kind,
            "original_name": original_name,
            "stored_path": stored_path,
            "metadata_json": json.dumps(metadata_dict),
            "created_at": now
        }
    )
    await db.commit()
    
    return asset_id


async def list_assets_async(
    user_id: str,
    kind: str,
    db: AsyncSession,
    search: Optional[str] = None,
    tags: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List assets for user by kind with optional filters
    
    Args:
        user_id: User ID
        kind: Asset kind ('job_description' or 'resume')
        db: Database session
        search: Full-text search query
        tags: List of tags to filter by (must have ALL)
        skills: List of skills to filter by (must have ANY)
        name: Filter by candidate name (partial match)
        
    Returns:
        List of asset dictionaries
    """
    result = await db.execute(
        text("""
            SELECT id, original_name, stored_path, metadata_json, created_at
            FROM file_assets
            WHERE user_id = :user_id AND kind = :kind
            ORDER BY created_at DESC
        """),
        {"user_id": user_id, "kind": kind}
    )
    rows = result.fetchall()
    
    assets = []
    for row in rows:
        assets.append({
            "id": row[0],
            "original_name": row[1],
            "stored_path": row[2],
            "metadata": _safe_json_loads(row[3] or "{}"),
            "created_at": row[4]
        })
    
    # Apply filters
    filtered_assets = assets
    search_lower = search.lower() if search else None
    name_lower = name.lower() if name else None
    tags = tags or []
    skills = skills or []
    
    if search_lower:
        # Full-text search across relevant fields
        filtered_assets = [
            asset for asset in filtered_assets
            if (
                search_lower in asset["original_name"].lower() or
                search_lower in asset["metadata"].get("name", "").lower() or
                any(search_lower in str(skill).lower() for skill in asset["metadata"].get("skills", [])) or
                any(search_lower in str(tag).lower() for tag in asset["metadata"].get("tags", [])) or
                any(search_lower in str(cert).lower() for cert in asset["metadata"].get("certifications", []))
            )
        ]
    
    if tags:
        # Must have ALL specified tags
        filtered_assets = [
            asset for asset in filtered_assets
            if all(tag.lower() in [t.lower() for t in asset["metadata"].get("tags", [])] for tag in tags)
        ]
    
    if skills:
        # Must have ANY of the specified skills (case-insensitive)
        filtered_assets = [
            asset for asset in filtered_assets
            if any(skill.lower() in [str(s).lower() for s in asset["metadata"].get("skills", [])] for skill in skills)
        ]
    
    if name_lower:
        # Partial match on candidate name (case-insensitive)
        filtered_assets = [
            asset for asset in filtered_assets
            if name_lower in asset["metadata"].get("name", "").lower()
        ]
    
    return filtered_assets


async def get_asset_async(
    asset_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Get asset by ID
    
    Args:
        asset_id: Asset ID
        db: Database session
        
    Returns:
        Asset dictionary or empty dict if not found
    """
    result = await db.execute(
        text("""
            SELECT id, original_name, stored_path, metadata_json, created_at, user_id, kind
            FROM file_assets
            WHERE id = :asset_id
        """),
        {"asset_id": asset_id}
    )
    row = result.fetchone()
    
    if not row:
        return {}
    
    return {
        "id": row[0],
        "original_name": row[1],
        "stored_path": row[2],
        "metadata": _safe_json_loads(row[3] or "{}"),
        "created_at": row[4],
        "user_id": row[5],
        "kind": row[6]
    }


async def delete_asset_async(
    asset_id: str,
    user_id: str,
    db: AsyncSession
) -> bool:
    """
    Delete asset (only if owned by user)
    
    Args:
        asset_id: Asset ID
        user_id: User ID (for authorization)
        db: Database session
        
    Returns:
        True if deleted, False if not found
    """
    result = await db.execute(
        text("""
            DELETE FROM file_assets
            WHERE id = :asset_id AND user_id = :user_id
        """),
        {"asset_id": asset_id, "user_id": user_id}
    )
    await db.commit()
    
    return result.rowcount > 0


async def update_asset_tags_async(
    asset_id: str,
    tags: List[str],
    user_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Update tags for an asset
    
    Args:
        asset_id: Asset ID
        tags: List of tags
        user_id: User ID (for authorization)
        db: Database session
        
    Returns:
        Updated asset dictionary or empty dict if not found
    """
    # First, get the asset to check ownership and get current metadata
    asset = await get_asset_async(asset_id, db)
    
    if not asset or asset["user_id"] != user_id:
        return {}
    
    # Update metadata with tags
    metadata = asset["metadata"]
    metadata["tags"] = tags
    
    # Update in database
    await db.execute(
        text("""
            UPDATE file_assets
            SET metadata_json = :metadata_json
            WHERE id = :asset_id AND user_id = :user_id
        """),
        {
            "asset_id": asset_id,
            "user_id": user_id,
            "metadata_json": json.dumps(metadata)
        }
    )
    await db.commit()
    
    # Return updated asset
    return await get_asset_async(asset_id, db)


def load_asset_content(asset: Dict[str, Any]) -> bytes:
    """
    Load asset file content
    
    Args:
        asset: Asset dictionary with stored_path
        
    Returns:
        File content as bytes
    """
    if not asset:
        return b""
    path = asset.get("stored_path")
    if not path or not Path(path).exists():
        return b""
    return Path(path).read_bytes()
