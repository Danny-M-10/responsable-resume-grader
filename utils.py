"""
Shared utility functions for the application.
"""

import os
from typing import Any


def prepare_query(conn: Any, query: str) -> str:
    """
    Prepare SQL query for database compatibility.
    Swaps SQLite-style placeholders (?) to psycopg2-style (%s) when using Postgres.
    
    Args:
        conn: Database connection object
        query: SQL query with ? placeholders
        
    Returns:
        Query string with appropriate placeholders for the database type
    """
    if conn.__class__.__module__.startswith("psycopg2"):
        return query.replace("?", "%s")
    return query


def is_safe_path(path: str, base_dir: str = None) -> bool:
    """
    Check if a file path is safe to access (prevents path traversal).
    
    Args:
        path: File path to validate
        base_dir: Base directory that path must be within (optional)
        
    Returns:
        True if path is safe, False otherwise
    """
    if not path:
        return False
    
    try:
        # Resolve to absolute path
        real_path = os.path.realpath(path)
        
        # If base_dir is provided, ensure path is within it
        if base_dir:
            real_base = os.path.realpath(base_dir)
            if not real_path.startswith(real_base):
                return False
        
        # Check for path traversal attempts
        if '..' in path or path.startswith('/') and not base_dir:
            # If no base_dir specified, reject absolute paths
            if not base_dir:
                return False
        
        return True
    except (OSError, ValueError):
        return False


# Constants
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_RESUME_EXTENSIONS = ['.pdf', '.docx', '.txt']
