"""
Async database initialization for FastAPI backend
Creates all required tables if they don't exist
"""
import os
import logging
from sqlalchemy import text
from backend.database.connection import engine

logger = logging.getLogger(__name__)

async def init_db_async():
    """
    Initialize all database tables asynchronously.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    async with engine.begin() as conn:
        # Create users table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """))
        
        # Create sessions table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity_at TEXT
            )
        """))
        
        # Create file_assets table (vault)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS file_assets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                kind TEXT NOT NULL CHECK (kind IN ('job_description','resume')),
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
        """))
        
        # Create jobs table (matches FastAPI API)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                location TEXT,
                parsed_data TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        
        # Create job_descriptions table (for compatibility with old schema)
        await conn.execute(text("""
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
            )
        """))
        
        # Create candidates table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                resume_path TEXT,
                parsed_data TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        
        # Create analyses table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                job_id TEXT NOT NULL,
                status TEXT NOT NULL,
                config TEXT,
                results TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        
        # Create reports table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                job_description_id TEXT REFERENCES job_descriptions(id) ON DELETE SET NULL,
                pdf_path TEXT NOT NULL,
                summary_json TEXT,
                created_at TEXT NOT NULL
            )
        """))
        
        # Create candidate_scores table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS candidate_scores (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                fit_score REAL,
                rationale TEXT,
                raw_json TEXT
            )
        """))
        
        # Create resumes table (for compatibility)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS resumes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                parsed_metadata_json TEXT,
                source_asset_id TEXT REFERENCES file_assets(id) ON DELETE SET NULL,
                uploaded_at TEXT NOT NULL
            )
        """))
        
        # Create candidate_profiles table
        await conn.execute(text("""
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
            )
        """))
        
        # Create resume_analyses table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS resume_analyses (
                candidate_profile_id TEXT NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
                report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                PRIMARY KEY (candidate_profile_id, report_id)
            )
        """))
        
        # Create password_reset_tokens table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL
            )
        """))
        
        # Create indexes for performance
        # Note: PostgreSQL doesn't support IF NOT EXISTS for indexes, so we check first
        indexes = [
            ("idx_users_email", "users", "email"),
            ("idx_sessions_token", "sessions", "token"),
            ("idx_sessions_user_id", "sessions", "user_id"),
            ("idx_file_assets_user_id", "file_assets", "user_id"),
            ("idx_jobs_user_id", "jobs", "user_id"),
            ("idx_candidates_user_id", "candidates", "user_id"),
            ("idx_analyses_user_id", "analyses", "user_id"),
            ("idx_analyses_job_id", "analyses", "job_id"),
            ("idx_reports_user_id", "reports", "user_id"),
            ("idx_reports_analysis_id", "reports", "analysis_id"),
        ]
        
        # Check if we're using PostgreSQL
        db_url = os.environ.get("DATABASE_URL", "")
        is_postgres = "postgres" in db_url.lower()
        
        for index_name, table_name, column_name in indexes:
            try:
                if is_postgres:
                    # Check if index exists in PostgreSQL
                    result = await conn.execute(text("""
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = :index_name AND tablename = :table_name
                    """), {"index_name": index_name, "table_name": table_name})
                    if not result.fetchone():
                        await conn.execute(text(f"CREATE INDEX {index_name} ON {table_name}({column_name})"))
                else:
                    # SQLite supports IF NOT EXISTS
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"))
            except Exception as e:
                # Index might already exist, ignore
                logger.debug(f"Index creation (may already exist): {e}")
        
        # Note: Using engine.begin() auto-commits when context exits
    
    logger.info("Database tables initialized successfully")
