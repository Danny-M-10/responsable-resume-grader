"""
Basic auth helper: email/password with hashed passwords and DB-backed sessions.
"""

import bcrypt
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from db import get_db, utcnow_str
from utils import prepare_query as _prepare_query

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SESSION_TTL_DAYS = 7
INACTIVITY_TIMEOUT_SECONDS = 2 * 60 * 60  # 2 hours
PASSWORD_RESET_EXPIRY_HOURS = 1
PASSWORD_RESET_RATE_LIMIT = 5  # Max requests per hour
PASSWORD_RESET_RATE_LIMIT_WINDOW_HOURS = 1


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_user(email: str, password: str) -> str:
    email = (email or "").strip().lower()
    if not email or not password:
        raise ValueError("Email and password are required.")
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format.")

    user_id = str(uuid.uuid4())
    password_hash = _hash_password(password)
    created_at = utcnow_str()

    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                _prepare_query(
                    conn,
                "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                ),
                (user_id, email, password_hash, created_at),
            )
            conn.commit()
        except Exception as e:
            # Likely unique constraint
            raise ValueError("User already exists or invalid data.") from e

    return user_id


def authenticate(email: str, password: str) -> Tuple[str, str]:
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    email = (email or "").strip().lower()
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format.")
    """
    Returns (session_token, user_id) if successful.
    """
    email = (email or "").strip().lower()
    if not email or not password:
        raise ValueError("Email and password are required.")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            _prepare_query(conn, "SELECT id, password_hash FROM users WHERE email = ?"),
            (email,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Invalid email or password.")

        user_id, password_hash = row[0], row[1]
        if not _verify_password(password, password_hash):
            raise ValueError("Invalid email or password.")

    session_token = create_session(user_id)
    return session_token, user_id


def create_session(user_id: str) -> str:
    token = str(uuid.uuid4())
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=SESSION_TTL_DAYS)
    last_activity = created_at.isoformat() + "Z"

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            _prepare_query(
                conn,
            "INSERT INTO sessions (token, user_id, created_at, expires_at, last_activity_at) VALUES (?, ?, ?, ?, ?)",
            ),
            (
                token,
                user_id,
                created_at.isoformat() + "Z",
                expires_at.isoformat() + "Z",
                last_activity,
            ),
        )
        conn.commit()

    return token


def update_session_activity(token: str) -> None:
    """
    Update the last_activity_at timestamp for a session.
    """
    if not token:
        return
    
    now_str = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            _prepare_query(conn, "UPDATE sessions SET last_activity_at = ? WHERE token = ?"),
            (now_str, token),
        )
        conn.commit()


def get_user_by_session(token: str) -> Optional[Tuple[str, str]]:
    """
    Returns (user_id, email) if session valid, not expired, and not timed out due to inactivity.
    Checks for 2-hour inactivity timeout.
    """
    if not token:
        return None

    now = datetime.utcnow()
    now_str = now.isoformat() + "Z"
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            _prepare_query(
                conn,
            """
            SELECT users.id, users.email, sessions.last_activity_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
              AND sessions.expires_at > ?
            """,
            ),
            (token, now_str),
        )
        row = cur.fetchone()
        if not row:
            return None
        
        user_id, email, last_activity_str = row[0], row[1], row[2]
        
        # Check inactivity timeout
        if last_activity_str:
            try:
                # Handle ISO format with Z
                if last_activity_str.endswith('Z'):
                    last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                else:
                    last_activity = datetime.fromisoformat(last_activity_str)
                
                # Convert to naive UTC datetime
                if last_activity.tzinfo:
                    last_activity = last_activity.replace(tzinfo=None)
                
                time_since_activity = (now - last_activity).total_seconds()
                if time_since_activity > INACTIVITY_TIMEOUT_SECONDS:
                    # Session expired due to inactivity, delete it
                    cur.execute(
                        _prepare_query(conn, "DELETE FROM sessions WHERE token = ?"),
                        (token,),
                    )
                    conn.commit()
                    return None
            except (ValueError, TypeError) as e:
                # If parsing fails, treat as no activity tracking (backward compatibility)
                # Log for debugging in production
                logger.warning(f"Failed to parse last_activity_at: {last_activity_str}, error: {e}", exc_info=True)
                pass
        
        return user_id, email


def destroy_session(token: str) -> None:
    if not token:
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            _prepare_query(conn, "DELETE FROM sessions WHERE token = ?"), (token,)
        )
        conn.commit()


def request_password_reset(email: str) -> Tuple[str, str]:
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    email = (email or "").strip().lower()
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format.")
    """
    Request password reset. Generates a reset token and stores it in DB.
    Returns (token, user_id) if user exists, raises ValueError if not.
    For code-based reset, token will be a 6-digit code.
    """
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Email is required.")
    
    # Check if user exists
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            _prepare_query(conn, "SELECT id FROM users WHERE email = ?"),
            (email,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("User not found.")
        user_id = row[0]
    
    # Check rate limiting - prevent abuse
    with get_db() as conn:
        cur = conn.cursor()
        # Count recent reset requests
        rate_limit_window = datetime.utcnow() - timedelta(hours=PASSWORD_RESET_RATE_LIMIT_WINDOW_HOURS)
        cur.execute(
            _prepare_query(conn, """
                SELECT COUNT(*) FROM password_reset_tokens
                WHERE user_id = ? AND created_at > ?
            """),
            (user_id, rate_limit_window.isoformat() + "Z"),
        )
        recent_count = cur.fetchone()[0]
        if recent_count >= PASSWORD_RESET_RATE_LIMIT:
            raise ValueError(f"Too many reset requests. Please wait before trying again. (Max {PASSWORD_RESET_RATE_LIMIT} per hour)")
        
        # Invalidate any existing reset tokens for this user
        cur.execute(
            _prepare_query(conn, "UPDATE password_reset_tokens SET used = TRUE WHERE user_id = ? AND used = FALSE"),
            (user_id,),
        )
        conn.commit()
    
    # Generate token (UUID for link, or 6-digit code)
    import random
    token = str(random.randint(100000, 999999))  # 6-digit code
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)
    
    with get_db() as conn:
        cur = conn.cursor()
        # Insert new token
        cur.execute(
            _prepare_query(
                conn,
                "INSERT INTO password_reset_tokens (token, user_id, expires_at, used, created_at) VALUES (?, ?, ?, ?, ?)"
            ),
            (token, user_id, expires_at.isoformat() + "Z", False, created_at.isoformat() + "Z"),
        )
        conn.commit()
    
    return token, user_id


def reset_password_with_token(token: str, new_password: str) -> bool:
    """
    Reset password using a reset token.
    Returns True if successful, False if token invalid/expired/used.
    Uses atomic update to prevent race conditions.
    """
    if not token or not new_password:
        return False
    
    now_str = datetime.utcnow().isoformat() + "Z"
    
    with get_db() as conn:
        try:
            cur = conn.cursor()
            # Atomically check and mark token as used, returning user_id if valid
            # This prevents race conditions where token could be used twice
            if conn.__class__.__module__.startswith("psycopg2"):
                # PostgreSQL - use RETURNING for atomic update
                cur.execute(
                    """
                    UPDATE password_reset_tokens 
                    SET used = TRUE 
                    WHERE token = %s AND expires_at > %s AND used = FALSE
                    RETURNING user_id
                    """,
                    (token, now_str),
                )
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    return False
                user_id = row[0]
            else:
                # SQLite - use separate queries but in same transaction
                cur.execute(
                    _prepare_query(conn, """
                        SELECT user_id FROM password_reset_tokens
                        WHERE token = ? AND expires_at > ? AND used = FALSE
                    """),
                    (token, now_str),
                )
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    return False
                user_id = row[0]
                # Mark as used
                cur.execute(
                    _prepare_query(conn, "UPDATE password_reset_tokens SET used = TRUE WHERE token = ?"),
                    (token,),
                )
            
            # Update password
            password_hash = _hash_password(new_password)
            cur.execute(
                _prepare_query(conn, "UPDATE users SET password_hash = ? WHERE id = ?"),
                (password_hash, user_id),
            )
            
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False


def reset_password_with_code(email: str, code: str, new_password: str) -> bool:
    """
    Reset password using email and 6-digit code.
    Returns True if successful, False if code invalid/expired/used.
    """
    email = (email or "").strip().lower()
    if not email or not code or not new_password:
        return False
    
    now_str = datetime.utcnow().isoformat() + "Z"
    
    with get_db() as conn:
        cur = conn.cursor()
        # Find user
        cur.execute(
            _prepare_query(conn, "SELECT id FROM users WHERE email = ?"),
            (email,),
        )
        user_row = cur.fetchone()
        if not user_row:
            return False
        user_id = user_row[0]
        
        # Find valid token/code
        cur.execute(
            _prepare_query(
                conn,
                """
                SELECT token FROM password_reset_tokens
                WHERE token = ? AND user_id = ? AND expires_at > ? AND used = FALSE
                """
            ),
            (code, user_id, now_str),
        )
        row = cur.fetchone()
        if not row:
            return False
        
        # Update password
        password_hash = _hash_password(new_password)
        cur.execute(
            _prepare_query(conn, "UPDATE users SET password_hash = ? WHERE id = ?"),
            (password_hash, user_id),
        )
        
        # Mark token as used
        cur.execute(
            _prepare_query(conn, "UPDATE password_reset_tokens SET used = TRUE WHERE token = ?"),
            (code,),
        )
        
        conn.commit()
        return True

