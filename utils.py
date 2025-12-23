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
        base_dir: Base directory that path must be within (optional, defaults to /app for containerized environments)
        
    Returns:
        True if path is safe, False otherwise
    """
    if not path:
        return False
    
    try:
        # Resolve to absolute path
        real_path = os.path.realpath(path)
        
        # Default base_dir to /app for containerized environments (AWS ECS)
        if not base_dir:
            # Check if we're in a containerized environment
            if os.path.exists('/app') and real_path.startswith('/app'):
                base_dir = '/app'
            elif os.path.exists(os.getcwd()):
                base_dir = os.getcwd()
            else:
                # If no base_dir and path is absolute, allow /app paths (containerized)
                if real_path.startswith('/app'):
                    return True
                # Otherwise reject absolute paths without base_dir
                return False
        
        # If base_dir is provided, ensure path is within it
        if base_dir:
            real_base = os.path.realpath(base_dir)
            if not real_path.startswith(real_base):
                return False
        
        # Check for path traversal attempts
        if '..' in path:
            return False
        
        return True
    except (OSError, ValueError):
        return False


# Constants
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_RESUME_EXTENSIONS = ['.pdf', '.docx', '.txt']
