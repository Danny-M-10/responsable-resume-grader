"""
Lightweight database helper with optional Postgres support.

- Uses DATABASE_URL env var if provided, otherwise defaults to local SQLite.
- Provides init_db() to create required tables.
- Keeps the interface minimal for use across app modules.
"""

import os
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, Optional, Tuple
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

Connection = sqlite3.Connection


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite://") or url == "" or url is None


def _parse_db_url(url: Optional[str]) -> Tuple[str, dict]:
    if not url:
        return "sqlite", {"path": os.path.join(os.getcwd(), "candidate_ranker.db")}

    parsed = urlparse(url)
    if parsed.scheme.startswith("postgres"):
        return "postgres", {"url": url}
    if parsed.scheme.startswith("sqlite"):
        path = parsed.path if parsed.path else os.path.join(os.getcwd(), "candidate_ranker.db")
        return "sqlite", {"path": path}
    # Fallback to sqlite if unknown
    return "sqlite", {"path": os.path.join(os.getcwd(), "candidate_ranker.db")}


@contextmanager
def get_db() -> Iterator[Connection]:
    """
    Provide a DB connection. For SQLite, enforces foreign keys.
    """
    db_url = os.environ.get("DATABASE_URL", "")
    db_type, cfg = _parse_db_url(db_url)

    if db_type == "postgres":
        try:
            import psycopg2
        except ImportError as exc:
            raise RuntimeError("psycopg2 is required for Postgres connections. Install psycopg2-binary.") from exc

        conn = psycopg2.connect(cfg["url"])
        try:
            yield conn
        finally:
            conn.close()
    else:
        # SQLite
        conn = sqlite3.connect(cfg["path"])
        conn.row_factory = sqlite3.Row
        try:
            # Enforce FK constraints
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        finally:
            conn.close()


def _create_tables_sql() -> list:
    """
    Returns SQL statements to create required tables if they don't exist.
    """
    return [
        # Users
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
        # Sessions
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            last_activity_at TEXT
        );
        """,
        # Stored file assets (common vault)
        """
        CREATE TABLE IF NOT EXISTS file_assets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            kind TEXT NOT NULL CHECK (kind IN ('job_description','resume')),
            original_name TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            metadata_json TEXT,
            created_at TEXT NOT NULL
        );
        """,
        # Job descriptions tied to runs
        """
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT,
            location TEXT,
            certifications_json TEXT,
            required_skills_json TEXT,
            preferred_skills_json TEXT,
            full_description TEXT,
            source_asset_id TEXT REFERENCES file_assets(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            avionte_job_id TEXT,
            avionte_sync_at TEXT
        );
        """,
        # Resumes uploaded for runs
        """
        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            original_name TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            parsed_metadata_json TEXT,
            source_asset_id TEXT REFERENCES file_assets(id) ON DELETE SET NULL,
            uploaded_at TEXT NOT NULL
        );
        """,
        # Reports generated
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_description_id TEXT REFERENCES job_descriptions(id) ON DELETE SET NULL,
            pdf_path TEXT NOT NULL,
            summary_json TEXT,
            created_at TEXT NOT NULL
        );
        """,
        # Candidate scores per report
        """
        CREATE TABLE IF NOT EXISTS candidate_scores (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            candidate_name TEXT,
            email TEXT,
            phone TEXT,
            fit_score REAL,
            rationale TEXT,
            raw_json TEXT
        );
        """,
        # Password reset tokens
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL
        );
        """,
        # Candidate profiles (resume database)
        """
        CREATE TABLE IF NOT EXISTS candidate_profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            resume_file_id TEXT REFERENCES file_assets(id) ON DELETE SET NULL,
            parsed_data_json TEXT,
            tags_json TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            avionte_talent_id TEXT,
            avionte_sync_at TEXT
        );
        """,
        # Resume analyses junction table (many-to-many)
        """
        CREATE TABLE IF NOT EXISTS resume_analyses (
            candidate_profile_id TEXT NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
            report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            PRIMARY KEY (candidate_profile_id, report_id)
        );
        """
    ]


def init_db() -> None:
    """
    Initialize database tables. Safe to run multiple times.
    """
    statements = _create_tables_sql()
    with get_db() as conn:
        cur = conn.cursor()
        for stmt in statements:
            cur.execute(stmt)
        
        # Migration: Add last_activity_at to sessions if it doesn't exist
        try:
            # Check if column exists (PostgreSQL)
            if conn.__class__.__module__.startswith("psycopg2"):
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='sessions' AND column_name='last_activity_at'
                """)
                if not cur.fetchone():
                    cur.execute("ALTER TABLE sessions ADD COLUMN last_activity_at TEXT")
                    # Set existing sessions to created_at as default
                    cur.execute("UPDATE sessions SET last_activity_at = created_at WHERE last_activity_at IS NULL")
            else:
                # SQLite - check if column exists
                cur.execute("PRAGMA table_info(sessions)")
                columns = [row[1] for row in cur.fetchall()]
                if 'last_activity_at' not in columns:
                    cur.execute("ALTER TABLE sessions ADD COLUMN last_activity_at TEXT")
                    # Set existing sessions to created_at as default
                    cur.execute("UPDATE sessions SET last_activity_at = created_at WHERE last_activity_at IS NULL")
        except Exception as e:
            # Column might already exist, ignore
            logger.debug(f"Migration check for last_activity_at: {e}")
            pass
        
        # Migration: Add Avionté columns to candidate_profiles if they don't exist
        try:
            if conn.__class__.__module__.startswith("psycopg2"):
                # PostgreSQL
                for column in ['avionte_talent_id', 'avionte_sync_at']:
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='candidate_profiles' AND column_name=%s
                    """, (column,))
                    if not cur.fetchone():
                        cur.execute(f"ALTER TABLE candidate_profiles ADD COLUMN {column} TEXT")
            else:
                # SQLite
                cur.execute("PRAGMA table_info(candidate_profiles)")
                columns = [row[1] for row in cur.fetchall()]
                if 'avionte_talent_id' not in columns:
                    cur.execute("ALTER TABLE candidate_profiles ADD COLUMN avionte_talent_id TEXT")
                if 'avionte_sync_at' not in columns:
                    cur.execute("ALTER TABLE candidate_profiles ADD COLUMN avionte_sync_at TEXT")
        except Exception as e:
            logger.debug(f"Migration check for candidate_profiles Avionté columns: {e}")
            pass
        
        # Migration: Add Avionté columns to job_descriptions if they don't exist
        try:
            if conn.__class__.__module__.startswith("psycopg2"):
                # PostgreSQL
                for column in ['avionte_job_id', 'avionte_sync_at']:
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='job_descriptions' AND column_name=%s
                    """, (column,))
                    if not cur.fetchone():
                        cur.execute(f"ALTER TABLE job_descriptions ADD COLUMN {column} TEXT")
            else:
                # SQLite
                cur.execute("PRAGMA table_info(job_descriptions)")
                columns = [row[1] for row in cur.fetchall()]
                if 'avionte_job_id' not in columns:
                    cur.execute("ALTER TABLE job_descriptions ADD COLUMN avionte_job_id TEXT")
                if 'avionte_sync_at' not in columns:
                    cur.execute("ALTER TABLE job_descriptions ADD COLUMN avionte_sync_at TEXT")
        except Exception as e:
            logger.debug(f"Migration check for job_descriptions Avionté columns: {e}")
            pass
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_scores_report_id ON candidate_scores(report_id);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_scores_fit_score ON candidate_scores(fit_score);",
            "CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);",
            "CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_job_descriptions_user_id ON job_descriptions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_file_assets_user_id ON file_assets(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user_id ON candidate_profiles(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user_id_name ON candidate_profiles(user_id, name);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user_id_email ON candidate_profiles(user_id, email);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user_id_created_at ON candidate_profiles(user_id, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_resume_analyses_candidate_profile_id ON resume_analyses(candidate_profile_id);",
            "CREATE INDEX IF NOT EXISTS idx_resume_analyses_report_id ON resume_analyses(report_id);",
            "CREATE INDEX IF NOT EXISTS idx_candidate_profiles_avionte_talent_id ON candidate_profiles(avionte_talent_id);",
            "CREATE INDEX IF NOT EXISTS idx_job_descriptions_avionte_job_id ON job_descriptions(avionte_job_id);",
        ]
        
        for index_stmt in indexes:
            try:
                # PostgreSQL uses slightly different syntax
                if conn.__class__.__module__.startswith("psycopg2"):
                    # PostgreSQL doesn't support IF NOT EXISTS for indexes, so check first
                    index_name = index_stmt.split("idx_")[1].split(" ")[0]
                    table_name = index_stmt.split("ON ")[1].split("(")[0].strip()
                    cur.execute("""
                        SELECT indexname FROM pg_indexes 
                        WHERE indexname = %s AND tablename = %s
                    """, (f"idx_{index_name}", table_name))
                    if not cur.fetchone():
                        # Remove IF NOT EXISTS for PostgreSQL
                        pg_stmt = index_stmt.replace(" IF NOT EXISTS", "")
                        cur.execute(pg_stmt)
                else:
                    # SQLite supports IF NOT EXISTS
                    cur.execute(index_stmt)
            except Exception as e:
                # Index might already exist or creation failed, ignore
                logger.debug(f"Index creation (may already exist): {e}")
                pass
        
        conn.commit()


def utcnow_str() -> str:
    return datetime.utcnow().isoformat() + "Z"


