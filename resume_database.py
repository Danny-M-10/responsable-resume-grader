"""
Resume Database Module
Manages candidate profiles stored in the database for reuse across analyses
"""

import json
import uuid
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from db import get_db, utcnow_str
from utils import prepare_query

logger = logging.getLogger(__name__)


def save_candidate_profile(
    user_id: str,
    resume_data: Dict[str, Any],
    resume_file_id: Optional[str] = None,
    tags: List[str] = None,
    notes: str = None
) -> str:
    """
    Save a parsed resume to the candidate profiles database
    
    Args:
        user_id: User ID who owns this profile
        resume_data: Parsed resume data (name, email, phone, location, skills, certifications, etc.)
        resume_file_id: Optional file_assets ID for the resume file
        tags: Optional list of tags for organization
        notes: Optional user notes about the candidate
    
    Returns:
        Profile ID
    """
    profile_id = str(uuid.uuid4())
    now = utcnow_str()
    
    with get_db() as conn:
        cur = conn.cursor()
        query = prepare_query(conn, """
            INSERT INTO candidate_profiles 
            (id, user_id, name, email, phone, location, resume_file_id, 
             parsed_data_json, tags_json, notes, created_at, updated_at,
             avionte_talent_id, avionte_sync_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        cur.execute(query, (
            profile_id,
            user_id,
            resume_data.get('name', ''),
            resume_data.get('email', ''),
            resume_data.get('phone', ''),
            resume_data.get('location', ''),
            resume_file_id,
            json.dumps(resume_data),
            json.dumps(tags or []),
            notes or '',
            now,
            now,
            None,  # avionte_talent_id (no longer used)
            None   # avionte_sync_at (no longer used)
        ))
        try:
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save candidate profile: {e}", exc_info=True)
            raise
    
    return profile_id


def get_candidate_profile(profile_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a candidate profile by ID
    
    Args:
        profile_id: Profile ID
        user_id: User ID (for security check)
    
    Returns:
        Profile dict or None if not found
    """
    with get_db() as conn:
        cur = conn.cursor()
        query = prepare_query(conn, """
            SELECT id, user_id, name, email, phone, location, resume_file_id,
                   parsed_data_json, tags_json, notes, created_at, updated_at
            FROM candidate_profiles
            WHERE id = ? AND user_id = ?
        """)
        cur.execute(query, (profile_id, user_id))
        row = cur.fetchone()
        
        if not row:
            return None
        
        (id, user_id_db, name, email, phone, location, resume_file_id,
         parsed_data_json, tags_json, notes, created_at, updated_at) = row
        
        try:
            parsed_data = json.loads(parsed_data_json) if parsed_data_json else {}
            tags = json.loads(tags_json) if tags_json else []
        except (json.JSONDecodeError, TypeError):
            parsed_data = {}
            tags = []
        
        return {
            'id': id,
            'user_id': user_id_db,
            'name': name or '',
            'email': email or '',
            'phone': phone or '',
            'location': location or '',
            'resume_file_id': resume_file_id,
            'parsed_data': parsed_data,
            'tags': tags,
            'notes': notes or '',
            'created_at': created_at,
            'updated_at': updated_at
        }


def search_candidates(
    user_id: str,
    query: str = "",
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search candidates by name, email, skills, certifications, etc.
    
    Args:
        user_id: User ID
        query: Search query string (searches name, email, skills, certifications)
        filters: Optional dict with filters (tags, date_range, experience_level, location)
    
    Returns:
        List of candidate profiles
    """
    filters = filters or {}
    profiles = []
    
    with get_db() as conn:
        cur = conn.cursor()
        
        # Build WHERE clause
        conditions = ["user_id = ?"]
        params = [user_id]
        
        # Search query
        if query:
            query_lower = query.lower()
            conditions.append("""
                (LOWER(name) LIKE ? OR 
                 LOWER(email) LIKE ? OR
                 LOWER(parsed_data_json) LIKE ?)
            """)
            search_pattern = f"%{query_lower}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Tag filter
        if filters.get('tags'):
            tags = filters['tags']
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                conditions.append("tags_json LIKE ?")
                params.append(f'%"{tag}"%')
        
        # Location filter
        if filters.get('location'):
            conditions.append("LOWER(location) LIKE ?")
            params.append(f"%{filters['location'].lower()}%")
        
        # Date range filter
        if filters.get('date_from'):
            conditions.append("created_at >= ?")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            conditions.append("created_at <= ?")
            params.append(filters['date_to'])
        
        where_clause = " AND ".join(conditions)
        base_query = """
            SELECT id, user_id, name, email, phone, location, resume_file_id,
                   parsed_data_json, tags_json, notes, created_at, updated_at
            FROM candidate_profiles
            WHERE {}
            ORDER BY created_at DESC
        """
        sql = prepare_query(conn, base_query.format(where_clause))
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        for row in rows:
            (id, user_id_db, name, email, phone, location, resume_file_id,
             parsed_data_json, tags_json, notes, created_at, updated_at) = row
            
            try:
                parsed_data = json.loads(parsed_data_json) if parsed_data_json else {}
                tags = json.loads(tags_json) if tags_json else []
            except (json.JSONDecodeError, TypeError):
                parsed_data = {}
                tags = []
            
            # Experience level filter (check in parsed_data)
            if filters.get('experience_level'):
                exp_level = filters['experience_level'].lower()
                candidate_years = parsed_data.get('years_of_experience', 0)
                if exp_level == 'junior' and candidate_years >= 3:
                    continue
                elif exp_level == 'mid' and (candidate_years < 3 or candidate_years >= 7):
                    continue
                elif exp_level == 'senior' and candidate_years < 7:
                    continue
            
            profiles.append({
                'id': id,
                'user_id': user_id_db,
                'name': name or '',
                'email': email or '',
                'phone': phone or '',
                'location': location or '',
                'resume_file_id': resume_file_id,
                'parsed_data': parsed_data,
                'tags': tags,
                'notes': notes or '',
                'created_at': created_at,
                'updated_at': updated_at
            })
    
    return profiles


def filter_candidates(
    user_id: str,
    tags: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    experience_level: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter candidates by various criteria
    
    Args:
        user_id: User ID
        tags: List of tags to filter by
        date_range: Dict with 'from' and 'to' dates
        experience_level: Experience level filter ("Junior", "Mid", "Senior")
        location: Location filter
    
    Returns:
        List of filtered candidate profiles
    """
    filters = {}
    if tags:
        filters['tags'] = tags
    if date_range:
        filters['date_from'] = date_range.get('from')
        filters['date_to'] = date_range.get('to')
    if experience_level:
        filters['experience_level'] = experience_level
    if location:
        filters['location'] = location
    
    return search_candidates(user_id, query="", filters=filters)


def update_candidate_profile(
    profile_id: str,
    user_id: str,
    updates: Dict[str, Any]
) -> bool:
    """
    Update a candidate profile (tags, notes, etc.)
    
    Args:
        profile_id: Profile ID
        user_id: User ID (for security check)
        updates: Dict with fields to update (tags, notes, etc.)
    
    Returns:
        True if updated, False if not found
    """
    with get_db() as conn:
        cur = conn.cursor()
        
        # Check if profile exists and belongs to user
        query = prepare_query(conn, """
            SELECT id FROM candidate_profiles
            WHERE id = ? AND user_id = ?
        """)
        cur.execute(query, (profile_id, user_id))
        if not cur.fetchone():
            return False
        
        # Build UPDATE statement
        set_clauses = []
        params = []
        
        if 'tags' in updates:
            set_clauses.append("tags_json = ?")
            params.append(json.dumps(updates['tags']))
        
        if 'notes' in updates:
            set_clauses.append("notes = ?")
            params.append(updates['notes'])
        
        if 'name' in updates:
            set_clauses.append("name = ?")
            params.append(updates['name'])
        
        if 'email' in updates:
            set_clauses.append("email = ?")
            params.append(updates['email'])
        
        if 'phone' in updates:
            set_clauses.append("phone = ?")
            params.append(updates['phone'])
        
        if 'location' in updates:
            set_clauses.append("location = ?")
            params.append(updates['location'])
        
        if not set_clauses:
            return True  # Nothing to update
        
        set_clauses.append("updated_at = ?")
        params.append(utcnow_str())
        params.extend([profile_id, user_id])
        
        base_update_query = """
            UPDATE candidate_profiles
            SET {}
            WHERE id = ? AND user_id = ?
        """
        update_sql = prepare_query(conn, base_update_query.format(', '.join(set_clauses)))
        
        cur.execute(update_sql, params)
        conn.commit()
        
        return True


def delete_candidate_profile(profile_id: str, user_id: str) -> bool:
    """
    Delete a candidate profile
    
    Args:
        profile_id: Profile ID
        user_id: User ID (for security check)
    
    Returns:
        True if deleted, False if not found
    """
    with get_db() as conn:
        cur = conn.cursor()
        query = prepare_query(conn, """
            DELETE FROM candidate_profiles
            WHERE id = ? AND user_id = ?
        """)
        cur.execute(query, (profile_id, user_id))
        try:
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete candidate profile: {e}", exc_info=True)
            raise
        
        return cur.rowcount > 0


def get_candidates_for_analysis(
    user_id: str,
    candidate_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Get multiple candidate profiles for use in an analysis
    
    Args:
        user_id: User ID
        candidate_ids: List of profile IDs
    
    Returns:
        List of candidate profiles with parsed_data ready for analysis
    """
    if not candidate_ids:
        return []
    
    profiles = []
    with get_db() as conn:
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(candidate_ids))
        query = prepare_query(conn, f"""
            SELECT id, name, email, phone, location, resume_file_id,
                   parsed_data_json, tags_json, notes, created_at, updated_at
            FROM candidate_profiles
            WHERE id IN ({placeholders}) AND user_id = ?
        """)
        params = list(candidate_ids) + [user_id]
        cur.execute(query, params)
        rows = cur.fetchall()
        
        for row in rows:
            (id, name, email, phone, location, resume_file_id,
             parsed_data_json, tags_json, notes, created_at, updated_at) = row
            
            try:
                parsed_data = json.loads(parsed_data_json) if parsed_data_json else {}
                tags = json.loads(tags_json) if tags_json else []
            except (json.JSONDecodeError, TypeError):
                parsed_data = {}
                tags = []
            
            profiles.append({
                'id': id,
                'name': name or '',
                'email': email or '',
                'phone': phone or '',
                'location': location or '',
                'resume_file_id': resume_file_id,
                'parsed_data': parsed_data,
                'tags': tags,
                'notes': notes or '',
                'created_at': created_at,
                'updated_at': updated_at
            })
    
    return profiles


def link_candidate_to_analysis(candidate_profile_id: str, report_id: str) -> bool:
    """
    Link a candidate profile to an analysis report
    
    Args:
        candidate_profile_id: Profile ID
        report_id: Report ID
    
    Returns:
        True if linked successfully
    """
    try:
        with get_db() as conn:
            cur = conn.cursor()
            query = prepare_query(conn, """
                INSERT OR IGNORE INTO resume_analyses 
                (candidate_profile_id, report_id, created_at)
                VALUES (?, ?, ?)
            """)
            cur.execute(query, (candidate_profile_id, report_id, utcnow_str()))
            try:
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to link candidate to analysis: {e}", exc_info=True)
                return False
    except Exception as e:
        logger.error(f"Error linking candidate to analysis: {e}", exc_info=True)
        return False


def get_candidate_analyses(candidate_profile_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all analyses that used a specific candidate profile
    
    Args:
        candidate_profile_id: Profile ID
        user_id: User ID (for security check)
    
    Returns:
        List of report summaries
    """
    with get_db() as conn:
        cur = conn.cursor()
        query = prepare_query(conn, """
            SELECT r.id, r.created_at, r.pdf_path, r.summary_json,
                   j.title, j.location
            FROM resume_analyses ra
            JOIN reports r ON ra.report_id = r.id
            JOIN job_descriptions j ON r.job_description_id = j.id
            WHERE ra.candidate_profile_id = ? AND r.user_id = ?
            ORDER BY r.created_at DESC
        """)
        cur.execute(query, (candidate_profile_id, user_id))
        rows = cur.fetchall()
        
        analyses = []
        for row in rows:
            (report_id, created_at, pdf_path, summary_json, title, location) = row
            try:
                summary = json.loads(summary_json) if summary_json else {}
            except (json.JSONDecodeError, TypeError):
                summary = {}
            
            analyses.append({
                'report_id': report_id,
                'created_at': created_at,
                'pdf_path': pdf_path,
                'title': title or 'Untitled',
                'location': location or 'Not specified',
                'summary': summary
            })
        
        return analyses

