#!/usr/bin/env python3
"""
Migration script to move analysis documents from old Streamlit schema to new FastAPI schema.

This script:
1. Reads analyses from old schema (reports, job_descriptions, candidate_scores)
2. Converts them to new schema (jobs, analyses, candidates)
3. Preserves all data including PDF paths and candidate scores

Usage:
    # Use production database (get DATABASE_URL from AWS SSM)
    export DATABASE_URL=$(aws ssm get-parameter --name "/recruiting-candidate-ranker/DATABASE_URL" --region us-east-2 --with-decryption --query 'Parameter.Value' --output text)
    python3 migrate_analyses.py

    # Or set DATABASE_URL directly
    DATABASE_URL=postgresql://user:pass@host:5432/dbname python3 migrate_analyses.py
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Check if DATABASE_URL is set, if not try to get from AWS SSM
if not os.environ.get("DATABASE_URL"):
    try:
        import subprocess
        result = subprocess.run(
            ["aws", "ssm", "get-parameter", 
             "--name", "/recruiting-candidate-ranker/DATABASE_URL",
             "--region", "us-east-2",
             "--with-decryption",
             "--query", "Parameter.Value",
             "--output", "text"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            os.environ["DATABASE_URL"] = result.stdout.strip()
            print(f"✓ Retrieved DATABASE_URL from AWS SSM")
        else:
            print("⚠ DATABASE_URL not set and could not retrieve from AWS SSM")
            print("  Please set DATABASE_URL environment variable or ensure AWS CLI is configured")
            sys.exit(1)
    except Exception as e:
        print(f"⚠ Could not retrieve DATABASE_URL from AWS SSM: {e}")
        print("  Please set DATABASE_URL environment variable manually")
        sys.exit(1)

# Import database connection (same database for both old and new schemas)
from db import get_db, init_db
from utils import prepare_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_user_id_by_email(email: str) -> Optional[str]:
    """Get user ID from email"""
    with get_db() as conn:
        cur = conn.cursor()
        query = prepare_query(conn, "SELECT id FROM users WHERE email = ?")
        cur.execute(query, (email.strip().lower(),))
        row = cur.fetchone()
        return row[0] if row else None


def migrate_user_analyses(email: str) -> Dict[str, Any]:
    """
    Migrate all analyses for a user from old schema to new schema
    
    Returns:
        Dict with migration stats: {'migrated': count, 'skipped': count, 'errors': count}
    """
    logger.info(f"Starting migration for user: {email}")
    
    # Get user ID (same users table for both schemas)
    user_id = get_user_id_by_email(email)
    if not user_id:
        logger.error(f"User {email} not found in database. Skipping migration.")
        return {'migrated': 0, 'skipped': 0, 'errors': 1, 'error_message': f'User not found: {email}'}
    
    logger.info(f"Found user_id: {user_id} for email: {email}")
    
    # Fetch all reports for this user from old schema
    with get_db() as conn:
        cur = conn.cursor()
        query = prepare_query(conn, """
            SELECT r.id, r.created_at, r.pdf_path, r.summary_json,
                   j.id as job_id, j.title, j.location, j.certifications_json,
                   j.required_skills_json, j.preferred_skills_json, j.full_description,
                   j.created_at as job_created_at
            FROM reports r
            JOIN job_descriptions j ON r.job_description_id = j.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        """)
        cur.execute(query, (user_id,))
        report_rows = cur.fetchall()
    
    logger.info(f"Found {len(report_rows)} reports to migrate for user {email}")
    
    stats = {'migrated': 0, 'skipped': 0, 'errors': 0, 'error_details': []}
    
    for report_row in report_rows:
        try:
            (report_id, report_created_at, pdf_path, summary_json, job_id_old, title, location,
             certs_json, req_skills_json, pref_skills_json, full_desc, job_created_at) = report_row
            
            # Check if this analysis already exists in new schema (avoid duplicates)
            with get_db() as conn:
                cur = conn.cursor()
                query = prepare_query(conn, """
                    SELECT id FROM analyses 
                    WHERE user_id = ? AND created_at = ?
                    LIMIT 1
                """)
                cur.execute(query, (user_id, report_created_at))
                existing = cur.fetchone()
                if existing:
                    logger.info(f"Analysis already exists (created_at={report_created_at}). Skipping.")
                    stats['skipped'] += 1
                    continue
            
            # Parse JSON fields
            try:
                summary = json.loads(summary_json) if summary_json else {}
            except (json.JSONDecodeError, TypeError):
                summary = {}
            
            certifications = []
            if certs_json:
                try:
                    certs_data = json.loads(certs_json)
                    certifications = [c for c in certs_data if isinstance(c, dict)]
                except (json.JSONDecodeError, TypeError):
                    pass
            
            required_skills = []
            if req_skills_json:
                try:
                    required_skills = json.loads(req_skills_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            preferred_skills = []
            if pref_skills_json:
                try:
                    preferred_skills = json.loads(pref_skills_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Create job in new schema (jobs table)
            new_job_id = str(uuid.uuid4())
            job_parsed_data = {
                'job_title': title or 'Untitled',
                'location': location or 'Not specified',
                'required_skills': required_skills,
                'preferred_skills': preferred_skills,
                'certifications': certifications,
                'full_description': full_desc or '',
                'experience_level': '',  # Not in old schema
                'industry_context': None,
                'soft_skills': None,
                'technical_stack': None
            }
            
            # Insert job
            with get_db() as conn:
                cur = conn.cursor()
                query = prepare_query(conn, """
                    INSERT INTO jobs (id, user_id, title, location, parsed_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """)
                cur.execute(query, (
                    new_job_id,
                    user_id,
                    title or 'Untitled',
                    location or 'Not specified',
                    json.dumps(job_parsed_data),
                    job_created_at or report_created_at,
                    report_created_at
                ))
                conn.commit()
            
            logger.debug(f"Created job: {new_job_id} ({title})")
            
            # Get candidate scores from old schema
            with get_db() as conn:
                cur = conn.cursor()
                query = prepare_query(conn, """
                    SELECT candidate_name, email, phone, fit_score, rationale, raw_json
                    FROM candidate_scores
                    WHERE report_id = ?
                    ORDER BY fit_score DESC
                """)
                cur.execute(query, (report_id,))
                score_rows = cur.fetchall()
            
            # Convert candidate scores to new format
            candidate_scores_list = []
            for score_row in score_rows:
                name, email, phone, fit_score, rationale, raw_json = score_row
                
                # Parse raw_json if available
                candidate_data = {}
                if raw_json:
                    try:
                        candidate_data = json.loads(raw_json)
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                candidate_scores_list.append({
                    'name': name or candidate_data.get('name', 'Unknown'),
                    'email': email or candidate_data.get('email', ''),
                    'phone': phone or candidate_data.get('phone', ''),
                    'fit_score': float(fit_score),
                    'rationale': rationale or candidate_data.get('rationale', ''),
                    'chain_of_thought': candidate_data.get('chain_of_thought', ''),
                    'certifications': candidate_data.get('certifications', []),
                    'experience_match': candidate_data.get('experience_match', {}),
                    'certification_match': candidate_data.get('certification_match', {}),
                    'skills_match': candidate_data.get('skills_match', {}),
                    'location_match': candidate_data.get('location_match', False),
                    'component_scores': candidate_data.get('component_scores', {}),
                    'calibration_applied': candidate_data.get('calibration_applied', False),
                    'calibration_factor': candidate_data.get('calibration_factor', 1.0)
                })
            
            # Create analysis in new schema
            new_analysis_id = str(uuid.uuid4())
            analysis_results = {
                'status': 'completed',
                'report_pdf_path': pdf_path,
                'candidate_scores': candidate_scores_list,
                'summary': summary
            }
            
            # Create analysis config (minimal, since old schema didn't store this)
            analysis_config = {
                'job_id': new_job_id,
                'candidate_ids': [],  # We don't have candidate IDs in old schema
                'industry_template': 'general',
                'custom_scoring_weights': None,
                'dealbreakers': None,
                'bias_reduction_enabled': False
            }
            
            with get_db() as conn:
                cur = conn.cursor()
                query = prepare_query(conn, """
                    INSERT INTO analyses (id, user_id, job_id, status, config, results, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """)
                cur.execute(query, (
                    new_analysis_id,
                    user_id,
                    new_job_id,
                    "completed",
                    json.dumps(analysis_config),
                    json.dumps(analysis_results),
                    report_created_at,
                    report_created_at
                ))
                conn.commit()
            
            logger.debug(f"Created analysis: {new_analysis_id} (report_id: {report_id})")
            
            # Try to update existing report with analysis_id if column exists
            # Note: Old reports table doesn't have analysis_id column, so we'll skip if it doesn't exist
            try:
                with get_db() as conn:
                    cur = conn.cursor()
                    # Check if analysis_id column exists first
                    has_analysis_id = False
                    if conn.__class__.__module__.startswith("psycopg2"):
                        # PostgreSQL
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'reports' AND column_name = 'analysis_id'
                        """)
                        has_analysis_id = cur.fetchone() is not None
                    else:
                        # SQLite
                        cur.execute("PRAGMA table_info(reports)")
                        columns = [row[1] for row in cur.fetchall()]
                        has_analysis_id = 'analysis_id' in columns
                    
                    if has_analysis_id:
                        query = prepare_query(conn, """
                            UPDATE reports SET analysis_id = ? WHERE id = ?
                        """)
                        cur.execute(query, (new_analysis_id, report_id))
                        conn.commit()
                        logger.debug(f"Updated report {report_id} with analysis_id: {new_analysis_id}")
            except Exception as e:
                # Reports table might not have analysis_id column, that's okay
                logger.debug(f"Could not update report entry with analysis_id (may not be needed): {e}")
            
            stats['migrated'] += 1
            logger.info(f"✓ Migrated analysis: {title} ({report_created_at[:10] if report_created_at else 'unknown date'})")
            
        except Exception as e:
            logger.error(f"Error migrating report {report_id}: {e}", exc_info=True)
            stats['errors'] += 1
            stats['error_details'].append(f"Report {report_id}: {str(e)}")
    
    logger.info(f"Migration complete for {email}: {stats['migrated']} migrated, {stats['skipped']} skipped, {stats['errors']} errors")
    return stats


def main():
    """Main migration function"""
    # Initialize database tables if needed
    logger.info("Initializing database tables...")
    try:
        init_db()
        logger.info("✓ Database tables initialized")
    except Exception as e:
        logger.warning(f"Database initialization warning (may already exist): {e}")
    
    emails = ["danny@crossroadcoach.com", "shannon@crossroadcoach.com"]
    
    logger.info("=" * 60)
    logger.info("Starting Analysis Migration from Old to New Schema")
    logger.info(f"Database: {os.environ.get('DATABASE_URL', 'local SQLite')[:50]}...")
    logger.info("=" * 60)
    
    total_stats = {'migrated': 0, 'skipped': 0, 'errors': 0, 'error_details': []}
    
    for email in emails:
        logger.info(f"\n{'='*60}")
        logger.info(f"Migrating analyses for: {email}")
        logger.info(f"{'='*60}")
        
        try:
            stats = migrate_user_analyses(email)
            total_stats['migrated'] += stats['migrated']
            total_stats['skipped'] += stats['skipped']
            total_stats['errors'] += stats['errors']
            if stats.get('error_details'):
                total_stats['error_details'].extend(stats['error_details'])
        except Exception as e:
            logger.error(f"Failed to migrate analyses for {email}: {e}", exc_info=True)
            total_stats['errors'] += 1
            total_stats['error_details'].append(f"{email}: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Total migrated: {total_stats['migrated']}")
    logger.info(f"Total skipped: {total_stats['skipped']}")
    logger.info(f"Total errors: {total_stats['errors']}")
    
    if total_stats['error_details']:
        logger.error("\nError details:")
        for error in total_stats['error_details']:
            logger.error(f"  - {error}")
    
    logger.info("\nMigration completed!")


if __name__ == "__main__":
    main()
