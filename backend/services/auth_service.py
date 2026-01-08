"""
Async authentication service
Refactored from auth.py for FastAPI
"""
import bcrypt
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.database.connection import get_db
from backend.middleware.auth import create_access_token

# Constants
SESSION_TTL_DAYS = 7
INACTIVITY_TIMEOUT_SECONDS = 2 * 60 * 60  # 2 hours


def _hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


async def create_user_async(email: str, password: str, db: AsyncSession) -> str:
    """
    Create a new user asynchronously
    
    Args:
        email: User email
        password: User password
        db: Database session
        
    Returns:
        User ID
        
    Raises:
        ValueError: If email/password invalid or user already exists
    """
    email = (email or "").strip().lower()
    if not email or not password:
        raise ValueError("Email and password are required.")
    
    if not _validate_email(email):
        raise ValueError("Invalid email format.")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    
    user_id = str(uuid.uuid4())
    password_hash = _hash_password(password)
    created_at = datetime.utcnow().isoformat() + "Z"
    
    try:
        await db.execute(
            text("""
                INSERT INTO users (id, email, password_hash, created_at)
                VALUES (:id, :email, :password_hash, :created_at)
            """),
            {
                "id": user_id,
                "email": email,
                "password_hash": password_hash,
                "created_at": created_at
            }
        )
        await db.commit()
        return user_id
    except Exception as e:
        await db.rollback()
        # Check if it's a unique constraint violation
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ValueError("User already exists.") from e
        raise ValueError("Failed to create user.") from e


async def authenticate_async(email: str, password: str, db: AsyncSession) -> Tuple[str, str]:
    """
    Authenticate user and return JWT token and user ID
    
    Args:
        email: User email
        password: User password
        db: Database session
        
    Returns:
        Tuple of (access_token, user_id)
        
    Raises:
        ValueError: If authentication fails
    """
    email = (email or "").strip().lower()
    if not email or not password:
        raise ValueError("Email and password are required.")
    
    if not _validate_email(email):
        raise ValueError("Invalid email format.")
    
    result = await db.execute(
        text("SELECT id, password_hash FROM users WHERE email = :email"),
        {"email": email}
    )
    row = result.fetchone()
    
    if not row:
        raise ValueError("Invalid email or password.")
    
    user_id, password_hash = row[0], row[1]
    
    if not _verify_password(password, password_hash):
        raise ValueError("Invalid email or password.")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user_id})
    
    # Update last activity (optional - can be done in middleware)
    await db.execute(
        text("""
            UPDATE sessions 
            SET last_activity_at = :last_activity
            WHERE user_id = :user_id AND expires_at > :now
        """),
        {
            "last_activity": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "now": datetime.utcnow().isoformat() + "Z"
        }
    )
    await db.commit()
    
    return access_token, user_id


async def get_user_by_id_async(user_id: str, db: AsyncSession) -> Optional[dict]:
    """
    Get user by ID
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User dict with id and email, or None if not found
    """
    result = await db.execute(
        text("SELECT id, email, created_at FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    
    if not row:
        return None
    
    return {
        "id": row[0],
        "email": row[1],
        "created_at": row[2]
    }

