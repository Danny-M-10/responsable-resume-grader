"""
Settings API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from sqlalchemy import text
import json

from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id

router = APIRouter()

# Default settings template
DEFAULT_SETTINGS = {
    "theme": "light",
    "preferences": {
        "notifications_enabled": True,
        "auto_save": True,
        "results_per_page": 10
    }
}


@router.get("/")
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get user settings

    Args:
        user_id: Current user ID
        db: Database session

    Returns:
        User settings
    """
    # Try to load from user_settings table
    result = await db.execute(
        text("SELECT settings_json FROM user_settings WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()

    if row and row[0]:
        try:
            settings = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            # Merge with defaults to ensure all keys exist
            merged = {**DEFAULT_SETTINGS, **settings}
            if "preferences" in settings:
                merged["preferences"] = {**DEFAULT_SETTINGS.get("preferences", {}), **settings.get("preferences", {})}
            return merged
        except (json.JSONDecodeError, TypeError):
            pass

    # Return default settings if none found
    return DEFAULT_SETTINGS


@router.put("/")
async def update_settings(
    settings: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update user settings

    Args:
        settings: Settings to update
        user_id: Current user ID
        db: Database session

    Returns:
        Updated settings
    """
    from datetime import datetime, timezone

    settings_json = json.dumps(settings)
    updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Check if settings exist for user
    result = await db.execute(
        text("SELECT user_id FROM user_settings WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    exists = result.fetchone() is not None

    if exists:
        # Update existing settings
        await db.execute(
            text("""
                UPDATE user_settings
                SET settings_json = :settings_json, updated_at = :updated_at
                WHERE user_id = :user_id
            """),
            {"user_id": user_id, "settings_json": settings_json, "updated_at": updated_at}
        )
    else:
        # Insert new settings
        await db.execute(
            text("""
                INSERT INTO user_settings (user_id, settings_json, created_at, updated_at)
                VALUES (:user_id, :settings_json, :created_at, :updated_at)
            """),
            {"user_id": user_id, "settings_json": settings_json, "created_at": updated_at, "updated_at": updated_at}
        )

    await db.commit()

    # Return merged settings with defaults
    merged = {**DEFAULT_SETTINGS, **settings}
    if "preferences" in settings:
        merged["preferences"] = {**DEFAULT_SETTINGS.get("preferences", {}), **settings.get("preferences", {})}
    return merged
