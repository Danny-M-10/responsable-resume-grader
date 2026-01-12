"""
Async analysis/scoring service
Refactored from candidate_ranker.py for FastAPI
"""
import asyncio
import logging
import threading
from typing import Dict, Any, List
from sqlalchemy import text
from candidate_ranker import CandidateRankerApp
from backend.websocket.progress import send_progress_update
from backend.database.connection import AsyncSessionLocal
import json
import os
import traceback

logger = logging.getLogger(__name__)

# #region agent log
def _log_debug(hypothesis_id, location, message, data=None):
    """Log debug info to CloudWatch via standard logger and NDJSON file"""
    try:
        import json
        import time
        data_str = json.dumps(data or {}) if data else "{}"
        logger.info(f"[HYP-{hypothesis_id}] {location}: {message} | {data_str}")
        # Also write to NDJSON file for debug mode
        log_entry = {
            "timestamp": int(time.time() * 1000),
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "debug-session",
            "runId": "initial",
            "hypothesisId": hypothesis_id
        }
        try:
            with open("/Users/danny/Documents/Cursor/Projects/internal_crossroads_Candidate_Ranking_Application_clone/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Silently fail if file write fails
    except Exception as e:
        logger.error(f"Failed to log debug info: {e}")
# #endregion agent log

async def run_analysis_async(
    analysis_id: str,
    job_id: str,
    candidate_ids: List[str],
    config: Dict[str, Any],
    client_id: str = "default",
    user_id: str = None
) -> Dict[str, Any]:
    """
    Run candidate analysis asynchronously with progress updates
    
    Args:
        analysis_id: Analysis ID to update
        job_id: Job ID
        candidate_ids: List of candidate IDs
        config: Analysis configuration (industry_template, weights, etc.)
        client_id: Client ID for WebSocket progress updates
        user_id: User ID for database queries
        
    Returns:
        Analysis results dictionary
    """
    try:
        # #region agent log
        _log_debug("A", "analysis_service.py:40", "run_analysis_async started", {"analysis_id": analysis_id, "job_id": job_id, "candidate_ids_count": len(candidate_ids), "client_id": client_id})
        # #endregion agent log
        await send_progress_update(client_id, "initializing", 0.05, message="Initializing analysis...")
        # #region agent log
        _log_debug("A", "analysis_service.py:43", "Progress update sent: initializing", {"client_id": client_id})
        # #endregion agent log
        
        # Load job from database
        from backend.database.connection import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            job_result = await db.execute(
                text("SELECT title, location, parsed_data FROM jobs WHERE id = :job_id AND user_id = :user_id"),
                {"job_id": job_id, "user_id": user_id}
            )
            job_row = job_result.fetchone()
            
            if not job_row:
                # #region agent log
                _log_debug("D", "analysis_service.py:53", "Job not found in database", {"job_id": job_id, "user_id": user_id})
                # #endregion agent log
                raise ValueError(f"Job {job_id} not found")
            
            job_title = job_row[0]
            location = job_row[1] or ""
            parsed_data_str = job_row[2] or "{}"
            # #region agent log
            _log_debug("D", "analysis_service.py:58", "Job data loaded", {"job_title": job_title, "location": location, "parsed_data_length": len(str(parsed_data_str))})
            # #endregion agent log
            
            # Parse job data - properly deserialize JSON string
            try:
                if isinstance(parsed_data_str, str):
                    if parsed_data_str.strip():
                        parsed_data = json.loads(parsed_data_str)
                    else:
                        parsed_data = {}
                elif isinstance(parsed_data_str, dict):
                    # Already a dictionary (shouldn't happen, but handle gracefully)
                    parsed_data = parsed_data_str
                else:
                    parsed_data = {}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse job parsed_data as JSON (job_id={job_id}): {e}")
                logger.warning(f"Raw data: {parsed_data_str[:200]}")  # Log first 200 chars for debugging
                parsed_data = {}
            except Exception as e:
                logger.error(f"Unexpected error parsing job parsed_data (job_id={job_id}): {e}")
                parsed_data = {}
            
            job_description = parsed_data.get("full_description", "")
            certifications = parsed_data.get("certifications", [])
            required_skills = parsed_data.get("required_skills", [])
            preferred_skills = parsed_data.get("preferred_skills", [])
        
        await send_progress_update(client_id, "loading_resumes", 0.10, message="Loading candidate resumes...")
        
        # Load candidates and resume files
        resume_files = []
        # Create mapping of candidate names/emails to IDs for later matching (outside db block for scope)
        candidate_id_map = {}  # Maps (name, email) to candidate_id
        async with AsyncSessionLocal() as db:
            # Validate candidate_ids - should never be empty at this point
            if not candidate_ids:
                # #region agent log
                _log_debug("D", "analysis_service.py:91", "Empty candidate_ids - validation failed", {})
                # #endregion agent log
                raise ValueError("candidate_ids cannot be empty - validation should have caught this")
            
            # Use proper PostgreSQL array syntax for asyncpg
            # Build query with IN clause
            placeholders = ','.join([f':id_{i}' for i in range(len(candidate_ids))])
            params = {f'id_{i}': cid for i, cid in enumerate(candidate_ids)}
            params['user_id'] = user_id
            # #region agent log
            _log_debug("D", "analysis_service.py:99", "Executing candidate query", {"candidate_count": len(candidate_ids), "placeholders": placeholders[:100]})
            # #endregion agent log
            
            # Load candidates with emails for mapping
            email_result = await db.execute(
                text(f"SELECT id, name, email, resume_path FROM candidates WHERE id IN ({placeholders}) AND user_id = :user_id"),
                params
            )
            candidate_rows = email_result.fetchall()
            # #region agent log
            _log_debug("D", "analysis_service.py:103", "Candidate query completed", {"rows_found": len(candidate_rows)})
            # #endregion agent log
            
            # Create mapping and collect resume files
            for row in candidate_rows:
                candidate_id, name, email, resume_path = row
                # Create mapping entries for name/email lookup
                name_lower = name.lower() if name else ""
                email_lower = email.lower() if email else ""
                candidate_id_map[(name_lower, email_lower)] = candidate_id
                candidate_id_map[(name_lower, "")] = candidate_id  # Fallback: name only
                if email_lower:
                    candidate_id_map[("", email_lower)] = candidate_id  # Fallback: email only
                
                if resume_path and os.path.exists(resume_path):
                    resume_files.append(resume_path)
                else:
                    logger.warning(f"Resume file not found for candidate {candidate_id}: {resume_path}")
            
            # #region agent log
            _log_debug("D", "analysis_service.py:131", "Resume files collected", {"valid_files": len(resume_files), "file_paths": resume_files[:3], "candidate_mappings": len(candidate_id_map)})
            # #endregion agent log
        
        if not resume_files:
            # #region agent log
            _log_debug("C", "analysis_service.py:114", "No valid resume files found", {"candidate_rows": len(candidate_rows)})
            # #endregion agent log
            raise ValueError("No valid resume files found for candidates")
        
        await send_progress_update(client_id, "initializing_ai", 0.15, message="Initializing AI components...")
        # #region agent log
        _log_debug("C", "analysis_service.py:118", "Initializing CandidateRankerApp", {})
        # #endregion agent log
        
        # Initialize analysis app
        app = CandidateRankerApp()
        # #region agent log
        _log_debug("C", "analysis_service.py:122", "CandidateRankerApp initialized", {})
        # #endregion agent log
        
        # Progress callback wrapper - needs to work from thread context
        # Store loop reference to properly schedule async tasks from thread
        # Use get_running_loop() instead of get_event_loop() to get the current async context's loop
        loop = asyncio.get_running_loop()
        # #region agent log
        _log_debug("A", "analysis_service.py:165", "Event loop obtained for progress callback", {"loop_type": type(loop).__name__, "loop_id": id(loop)})
        # #endregion agent log
        def progress_callback(step, progress, current, total):
            # #region agent log
            loop_closed = False
            try:
                loop_closed = loop.is_closed() if hasattr(loop, 'is_closed') else False
            except:
                loop_closed = True  # Assume closed if we can't check
            _log_debug("A", "analysis_service.py:172", "Progress callback invoked", {"step": step, "progress": progress, "current": current, "total": total, "has_loop": loop is not None, "loop_closed": loop_closed, "thread_name": threading.current_thread().name})
            # #endregion agent log
            try:
                # Use run_coroutine_threadsafe to properly schedule coroutine from thread context
                if loop is None:
                    logger.warning("Event loop is None in progress callback")
                    return
                
                if loop_closed:
                    # #region agent log
                    _log_debug("A", "analysis_service.py:182", "Loop is closed, cannot send progress", {"step": step})
                    # #endregion agent log
                    logger.warning("Event loop is closed, cannot send progress update")
                    return
                
                # Schedule the coroutine from the thread context
                future = asyncio.run_coroutine_threadsafe(
                    send_progress_update(
                        client_id,
                        step,
                        progress,
                        current,
                        total,
                        message=f"Processing: {step}"
                    ),
                    loop
                )
                # #region agent log
                _log_debug("A", "analysis_service.py:199", "Progress update scheduled via run_coroutine_threadsafe", {"step": step, "progress": progress, "future_done": future.done()})
                # #endregion agent log
                # Don't wait for result (fire and forget from thread)
                # Optional: add a callback to log if it fails
                def log_result(fut):
                    # Since we're in a done callback, the future is already done
                    # Call result() without timeout to check for exceptions
                    try:
                        fut.result()  # Will raise if future was cancelled or had an exception
                    except Exception as e:
                        logger.warning(f"Progress update future failed: {e}", exc_info=True)
                future.add_done_callback(log_result)
            except RuntimeError as e:
                # Handle "Event loop is closed" or "no running event loop" errors
                # #region agent log
                _log_debug("A", "analysis_service.py:213", "Progress callback RuntimeError", {"error": str(e), "error_type": type(e).__name__})
                # #endregion agent log
                logger.warning(f"RuntimeError in progress callback (likely loop closed): {e}")
            except Exception as e:
                # #region agent log
                _log_debug("A", "analysis_service.py:218", "Progress callback error", {"error": str(e), "error_type": type(e).__name__, "traceback": traceback.format_exc()[:200]})
                # #endregion agent log
                logger.error(f"Error in progress callback: {e}", exc_info=True)
        
        await send_progress_update(client_id, "scoring", 0.20, message="Starting candidate scoring...")
        # #region agent log
        _log_debug("C", "analysis_service.py:161", "Starting thread pool executor", {"resume_count": len(resume_files)})
        # #endregion agent log
        
        # Run analysis in thread pool to avoid blocking event loop
        # Use a wrapper function to capture both pdf_path and candidate_scores
        def run_analysis_with_results():
            pdf_path_result = app.run(
                job_title=job_title,
                certifications=certifications,
                location=location,
                job_description=job_description,
                resume_files=resume_files,
                required_skills=required_skills if required_skills else None,
                preferred_skills=preferred_skills if preferred_skills else None,
                progress_callback=progress_callback,
                user_id=user_id,
                industry_template=config.get("industry_template", "general"),
                custom_scoring_weights=config.get("custom_scoring_weights"),
                dealbreakers=config.get("dealbreakers"),
                bias_reduction_enabled=config.get("bias_reduction_enabled", False)
            )
            # Access candidate_scores after run() completes
            candidate_scores = app.candidate_scores
            return pdf_path_result, candidate_scores
        
        # #region agent log
        _log_debug("B", "analysis_service.py:272", "Starting thread executor for analysis", {"resume_count": len(resume_files), "analysis_id": analysis_id})
        # #endregion agent log
        try:
            pdf_path, candidate_scores_list = await loop.run_in_executor(None, run_analysis_with_results)
            # #region agent log
            _log_debug("B", "analysis_service.py:275", "Thread executor completed successfully", {"pdf_path": pdf_path if pdf_path else None, "candidate_count": len(candidate_scores_list) if candidate_scores_list else 0, "candidate_id_map_size": len(candidate_id_map)})
            # #endregion agent log
        except Exception as executor_error:
            # #region agent log
            _log_debug("B", "analysis_service.py:278", "Thread executor failed with exception", {"error": str(executor_error), "error_type": type(executor_error).__name__, "traceback": traceback.format_exc()[:500]})
            # #endregion agent log
            raise
        
        await send_progress_update(client_id, "saving_results", 0.95, message="Saving analysis results...")
        
        # Convert candidate scores to JSON-serializable format
        from dataclasses import asdict
        candidates_data = []
        # #region agent log
        _log_debug("C", "analysis_service.py:278", "Starting candidate score serialization", {"candidate_scores_list_length": len(candidate_scores_list) if candidate_scores_list else 0, "candidate_id_map_keys": len(candidate_id_map)})
        # #endregion agent log
        if candidate_scores_list:
            for candidate_score in candidate_scores_list:
                try:
                    # Convert CandidateScore dataclass to dict
                    candidate_dict = asdict(candidate_score)
                    # Try to match to database candidate ID using name/email
                    candidate_email = candidate_dict.get("email", "").lower() if candidate_dict.get("email") else ""
                    candidate_name = candidate_dict.get("name", "").lower() if candidate_dict.get("name") else ""
                    # Look up candidate ID from mapping (created earlier)
                    candidate_id = candidate_id_map.get((candidate_name, candidate_email)) or candidate_id_map.get((candidate_name, "")) or candidate_id_map.get(("", candidate_email))
                    if not candidate_id:
                        # Fallback: use email if available, otherwise generate from name
                        if candidate_email:
                            candidate_id = candidate_email
                        else:
                            # Fallback: use name-based ID (sanitize for ID usage)
                            candidate_id = f"candidate-{abs(hash(candidate_name))}"
                    # Ensure all fields are JSON-serializable
                    candidates_data.append({
                        "id": str(candidate_id),  # Ensure it's a string
                        "name": candidate_dict.get("name", ""),
                        "email": candidate_dict.get("email", ""),
                        "phone": candidate_dict.get("phone", ""),
                        "fit_score": float(candidate_dict.get("fit_score", 0.0)),
                        "score": float(candidate_dict.get("fit_score", 0.0)),  # Alias for frontend compatibility
                        "certifications": candidate_dict.get("certifications", []),
                        "rationale": candidate_dict.get("rationale", ""),
                        "chain_of_thought": candidate_dict.get("chain_of_thought", ""),
                        "experience_match": candidate_dict.get("experience_match", {}),
                        "certification_match": candidate_dict.get("certification_match", {}),
                        "skills_match": candidate_dict.get("skills_match", {}),
                        "location_match": candidate_dict.get("location_match", False),
                        "transferrable_skills_match": candidate_dict.get("transferrable_skills_match", {}),
                        "component_scores": candidate_dict.get("component_scores", {})
                    })
                except Exception as e:
                    # #region agent log
                    _log_debug("C", "analysis_service.py:277", "Error serializing candidate score", {"error": str(e), "candidate_name": getattr(candidate_score, 'name', 'unknown')})
                    # #endregion agent log
                    logger.warning(f"Failed to serialize candidate score: {e}", exc_info=True)
        
        # Load results from the generated report/cache
        results = {
            "pdf_path": pdf_path,
            "status": "completed",
            "candidates": candidates_data  # Include candidate scores
        }
        # #region agent log
        _log_debug("C", "analysis_service.py:325", "Results prepared for saving", {"candidate_count": len(candidates_data), "has_pdf": bool(pdf_path), "results_keys": list(results.keys())})
        # #endregion agent log
        
        # Update analysis record in database
        # #region agent log
        _log_debug("B", "analysis_service.py:338", "Before database update to mark completed", {"analysis_id": analysis_id, "results_keys": list(results.keys()) if results else None, "candidate_count": len(results.get("candidates", [])) if results else 0})
        # #endregion agent log
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    UPDATE analyses 
                    SET status = 'completed', results = :results, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :analysis_id
                """),
                {"analysis_id": analysis_id, "results": json.dumps(results)}
            )
            # #region agent log
            _log_debug("B", "analysis_service.py:348", "Database UPDATE executed, before commit", {"analysis_id": analysis_id})
            # #endregion agent log
            await db.commit()
            # #region agent log
            _log_debug("B", "analysis_service.py:351", "Database commit completed", {"analysis_id": analysis_id})
            # #endregion agent log
        
        # #region agent log
        _log_debug("B", "analysis_service.py:354", "Before sending final progress update", {"client_id": client_id, "analysis_id": analysis_id})
        # #endregion agent log
        await send_progress_update(client_id, "complete", 1.0, message="Analysis complete!")
        # #region agent log
        _log_debug("B", "analysis_service.py:357", "Final progress update sent", {"client_id": client_id, "analysis_id": analysis_id})
        # #endregion agent log
        
        # #region agent log
        _log_debug("B", "analysis_service.py:360", "About to return results", {"analysis_id": analysis_id, "has_results": bool(results)})
        # #endregion agent log
        return results
        
    except Exception as e:
        # #region agent log
        _log_debug("E", "analysis_service.py:365", "Analysis exception caught in outer handler", {"error": str(e), "error_type": type(e).__name__, "analysis_id": analysis_id, "client_id": client_id, "traceback": traceback.format_exc()[:800]})
        # #endregion agent log
        logger.error(f"Analysis failed: {e}", exc_info=True)
        
        # Update analysis status to failed
        # #region agent log
        _log_debug("E", "analysis_service.py:370", "Attempting to update analysis status to failed", {"analysis_id": analysis_id})
        # #endregion agent log
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    text("""
                        UPDATE analyses 
                        SET status = 'failed', results = :results, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :analysis_id
                    """),
                    {"analysis_id": analysis_id, "results": json.dumps({"error": str(e)})}
                )
                await db.commit()
                # #region agent log
                _log_debug("E", "analysis_service.py:383", "Analysis status updated to failed in database", {"analysis_id": analysis_id})
                # #endregion agent log
        except Exception as db_err:
            # #region agent log
            _log_debug("E", "analysis_service.py:386", "Failed to update analysis status in DB", {"db_error": str(db_err), "analysis_id": analysis_id, "traceback": traceback.format_exc()[:500]})
            # #endregion agent log
            logger.error(f"Failed to update analysis status: {db_err}")
        
        # #region agent log
        _log_debug("E", "analysis_service.py:390", "Before sending error progress update", {"client_id": client_id})
        # #endregion agent log
        await send_progress_update(client_id, "error", 0.0, message=f"Analysis failed: {str(e)}")
        # #region agent log
        _log_debug("E", "analysis_service.py:393", "Error progress update sent, about to re-raise exception", {"client_id": client_id})
        # #endregion agent log
        raise

