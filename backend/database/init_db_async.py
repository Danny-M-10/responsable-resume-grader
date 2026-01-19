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
    # Use begin() for auto-commit on successful completion
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
        # Note: Must be created after users table exists
        try:
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
            logger.debug("✓ jobs table created/verified")
        except Exception as e:
            logger.error(f"Failed to create jobs table: {e}")
            raise
        
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
        try:
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
            logger.debug("✓ candidates table created/verified")
        except Exception as e:
            logger.error(f"Failed to create candidates table: {e}")
            # Don't raise - verification will catch and fix it
        
        # Create analyses table
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    job_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config TEXT,
                    results TEXT,
                    client_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))
            logger.debug("✓ analyses table created/verified")
        except Exception as e:
            logger.error(f"Failed to create analyses table: {e}")
            # Don't raise - verification will catch and fix it
        
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

        # Create user_settings table for settings persistence
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                settings_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
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
                    # For PostgreSQL, check if index exists first
                    check_result = await conn.execute(text("""
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = :index_name AND tablename = :table_name
                    """), {"index_name": index_name, "table_name": table_name})
                    row = check_result.fetchone()
                    if not row:
                        # Index doesn't exist, create it
                        await conn.execute(text(f"CREATE INDEX {index_name} ON {table_name}({column_name})"))
                else:
                    # SQLite supports IF NOT EXISTS
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"))
            except Exception as e:
                # Index might already exist or check failed, try to create anyway
                try:
                    if is_postgres:
                        await conn.execute(text(f"CREATE INDEX {index_name} ON {table_name}({column_name})"))
                    else:
                        await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"))
                except Exception as e2:
                    # Index likely already exists, ignore
                    logger.debug(f"Index {index_name} creation skipped (may already exist): {e2}")
        
        # engine.begin() auto-commits when context exits successfully
    
    # Verify critical tables exist
    # Check database type to use appropriate query
    db_url = os.environ.get("DATABASE_URL", "")
    is_postgres = "postgres" in db_url.lower()
    
    async with engine.begin() as conn:
        if is_postgres:
            # PostgreSQL uses information_schema
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'jobs', 'file_assets', 'analyses', 'candidates')
            """))
        else:
            # SQLite uses sqlite_master
            result = await conn.execute(text("""
                SELECT name as table_name 
                FROM sqlite_master 
                WHERE type = 'table' 
                AND name IN ('users', 'jobs', 'file_assets', 'analyses', 'candidates')
            """))
        existing_tables = {row[0] for row in result.fetchall()}
        expected_tables = {'users', 'jobs', 'file_assets', 'analyses', 'candidates'}
        missing_tables = expected_tables - existing_tables
        
        if missing_tables:
            logger.error(f"CRITICAL: Missing tables after initialization: {missing_tables}")
            logger.error("Attempting to create missing tables...")
            
            # Re-attempt to create missing tables
            for table_name in missing_tables:
                if table_name == 'jobs':
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
                elif table_name == 'candidates':
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
                elif table_name == 'analyses':
                    await conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS analyses (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            job_id TEXT NOT NULL,
                            status TEXT NOT NULL,
                            config TEXT,
                            results TEXT,
                            client_id TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                    """))
                elif table_name == 'file_assets':
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
            # engine.begin() auto-commits when context exits successfully
            logger.warning(f"Re-created missing tables: {missing_tables}")
        else:
            logger.info(f"✓ Verified all critical tables exist: {sorted(existing_tables)}")
        
        # Migration: Add client_id column to analyses table if it doesn't exist
        try:
            # Check if client_id column exists in analyses table
            is_postgres = 'postgresql' in str(engine.url).lower()
            if is_postgres:
                # PostgreSQL: Check information_schema.columns
                col_check = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'analyses' AND column_name = 'client_id'
                """))
                has_column = col_check.fetchone() is not None
            else:
                # SQLite: Check table schema
                table_info = await conn.execute(text("PRAGMA table_info(analyses)"))
                columns = [row[1] for row in table_info.fetchall()]
                has_column = 'client_id' in columns
            
            if not has_column:
                logger.info("Adding client_id column to analyses table (migration)...")
                await conn.execute(text("ALTER TABLE analyses ADD COLUMN client_id TEXT"))
                # Note: engine.begin() auto-commits on successful exit, no explicit commit needed
                logger.info("✓ Successfully added client_id column to analyses table")
            else:
                logger.debug("✓ client_id column already exists in analyses table")
        except Exception as e:
            logger.warning(f"Failed to add client_id column to analyses table (may already exist): {e}")
            # Don't fail initialization if migration fails - column might already exist

    # Migration: Clean up orphaned file_assets (local paths that no longer exist after S3 migration)
    async with engine.begin() as conn:
        try:
            # Delete file_assets with local paths (not S3) since files were lost during container deployments
            result = await conn.execute(
                text("DELETE FROM file_assets WHERE stored_path NOT LIKE 's3://%'")
            )
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"✓ Cleaned up {deleted_count} orphaned file_assets records (local paths migrated to S3)")
            else:
                logger.debug("✓ No orphaned file_assets to clean up")
        except Exception as e:
            logger.warning(f"Failed to clean up orphaned file_assets: {e}")

    # Migration: Clean up orphaned analyses (with local PDF paths that no longer exist)
    async with engine.begin() as conn:
        try:
            # Delete analyses where the pdf_path in results is a local path (not S3)
            # These are orphaned because the PDF files were lost during container deployments
            result = await conn.execute(
                text("""
                    DELETE FROM analyses
                    WHERE results IS NOT NULL
                    AND results::text LIKE '%"pdf_path": "storage/%'
                    AND results::text NOT LIKE '%"pdf_path": "s3://%'
                """)
            )
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"✓ Cleaned up {deleted_count} orphaned analyses with local PDF paths")
            else:
                logger.debug("✓ No orphaned analyses to clean up")
        except Exception as e:
            logger.warning(f"Failed to clean up orphaned analyses: {e}")

    logger.info("Database tables initialized successfully")
