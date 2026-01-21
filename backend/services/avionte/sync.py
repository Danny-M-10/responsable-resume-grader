"""
Avionté Synchronization Service
Handles syncing data between internal system and Avionté
"""
import logging
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .client import AvionteClient
from .talent import AvionteTalentAPI
from .jobs import AvionteJobsAPI
from .transformers import (
    transform_candidate_to_avionte_talent,
    transform_avionte_talent_to_candidate,
    transform_job_to_avionte_job,
    transform_avionte_job_to_job,
)
from .exceptions import AvionteException

logger = logging.getLogger(__name__)


class AvionteSyncService:
    """Synchronization service for Avionté integration"""
    
    def __init__(self, client: AvionteClient, db: AsyncSession):
        """
        Initialize sync service
        
        Args:
            client: Avionté API client
            db: Database session
        """
        self.client = client
        self.db = db
        self.talent_api = AvionteTalentAPI(client)
        self.jobs_api = AvionteJobsAPI(client)
    
    async def sync_candidate_to_avionte(
        self,
        candidate_id: str,
        user_id: str,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Sync a candidate to Avionté
        
        Args:
            candidate_id: Internal candidate ID
            user_id: User ID
            force_update: Force update even if already synced
            
        Returns:
            Sync result with Avionté talent ID
        """
        # Get candidate from database
        result = await self.db.execute(
            text("""
                SELECT id, name, email, phone, mobile, skills, certifications,
                       work_history, education, avionte_talent_id, avionte_sync_at
                FROM candidate_profiles
                WHERE id = :candidate_id AND user_id = :user_id
            """),
            {"candidate_id": candidate_id, "user_id": user_id}
        )
        candidate = result.fetchone()
        
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        candidate_dict = dict(candidate._mapping)
        
        # Check if already synced and not forcing update
        if not force_update and candidate_dict.get("avionte_talent_id"):
            logger.info(f"Candidate {candidate_id} already synced to Avionté")
            return {
                "success": True,
                "avionte_talent_id": candidate_dict["avionte_talent_id"],
                "action": "skipped"
            }
        
        # Transform to Avionté format
        talent = transform_candidate_to_avionte_talent(candidate_dict)
        
        try:
            # Create or update in Avionté
            if candidate_dict.get("avionte_talent_id"):
                # Update existing
                result = await self.talent_api.update_talent(
                    candidate_dict["avionte_talent_id"],
                    talent
                )
                action = "updated"
            else:
                # Create new
                result = await self.talent_api.create_talent(talent)
                action = "created"
            
            avionte_talent_id = result.get("talentId") or result.get("id")
            
            # Update database with Avionté ID and sync timestamp
            await self.db.execute(
                text("""
                    UPDATE candidate_profiles
                    SET avionte_talent_id = :talent_id,
                        avionte_sync_at = :sync_at
                    WHERE id = :candidate_id
                """),
                {
                    "talent_id": avionte_talent_id,
                    "sync_at": datetime.now(timezone.utc).isoformat(),
                    "candidate_id": candidate_id
                }
            )
            await self.db.commit()
            
            logger.info(f"Successfully synced candidate {candidate_id} to Avionté (action: {action})")
            
            return {
                "success": True,
                "avionte_talent_id": avionte_talent_id,
                "action": action
            }
            
        except AvionteException as e:
            logger.error(f"Failed to sync candidate {candidate_id} to Avionté: {str(e)}")
            await self.db.rollback()
            raise
    
    async def sync_job_to_avionte(
        self,
        job_id: str,
        user_id: str,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Sync a job to Avionté
        
        Args:
            job_id: Internal job ID
            user_id: User ID
            force_update: Force update even if already synced
            
        Returns:
            Sync result with Avionté job ID
        """
        # Get job from database
        result = await self.db.execute(
            text("""
                SELECT id, title, location, full_description, required_skills_json,
                       certifications_json, avionte_job_id, avionte_sync_at
                FROM job_descriptions
                WHERE id = :job_id AND user_id = :user_id
            """),
            {"job_id": job_id, "user_id": user_id}
        )
        job = result.fetchone()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job_dict = dict(job._mapping)
        
        # Parse JSON fields
        import json
        if job_dict.get("required_skills_json"):
            job_dict["required_skills"] = json.loads(job_dict["required_skills_json"])
        if job_dict.get("certifications_json"):
            job_dict["certifications"] = json.loads(job_dict["certifications_json"])
        
        # Check if already synced and not forcing update
        if not force_update and job_dict.get("avionte_job_id"):
            logger.info(f"Job {job_id} already synced to Avionté")
            return {
                "success": True,
                "avionte_job_id": job_dict["avionte_job_id"],
                "action": "skipped"
            }
        
        # Transform to Avionté format
        avionte_job = transform_job_to_avionte_job(job_dict)
        
        try:
            # Create or update in Avionté
            if job_dict.get("avionte_job_id"):
                # Update existing
                result = await self.jobs_api.update_job(
                    job_dict["avionte_job_id"],
                    avionte_job
                )
                action = "updated"
            else:
                # Create new
                result = await self.jobs_api.create_job(avionte_job)
                action = "created"
            
            avionte_job_id = result.get("jobId") or result.get("id")
            
            # Update database with Avionté ID and sync timestamp
            await self.db.execute(
                text("""
                    UPDATE job_descriptions
                    SET avionte_job_id = :job_id,
                        avionte_sync_at = :sync_at
                    WHERE id = :internal_job_id
                """),
                {
                    "job_id": avionte_job_id,
                    "sync_at": datetime.now(timezone.utc).isoformat(),
                    "internal_job_id": job_id
                }
            )
            await self.db.commit()
            
            logger.info(f"Successfully synced job {job_id} to Avionté (action: {action})")
            
            return {
                "success": True,
                "avionte_job_id": avionte_job_id,
                "action": action
            }
            
        except AvionteException as e:
            logger.error(f"Failed to sync job {job_id} to Avionté: {str(e)}")
            await self.db.rollback()
            raise
    
    async def sync_from_avionte_talent(
        self,
        talent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Sync a talent from Avionté to internal system
        
        Args:
            talent_id: Avionté talent ID
            user_id: User ID
            
        Returns:
            Sync result with internal candidate ID
        """
        try:
            # Get talent from Avionté
            talent_data = await self.talent_api.get_talent(talent_id)
            
            # Transform to internal format
            candidate = transform_avionte_talent_to_candidate(talent_data)
            
            # Check if candidate already exists
            result = await self.db.execute(
                text("""
                    SELECT id FROM candidate_profiles
                    WHERE avionte_talent_id = :talent_id AND user_id = :user_id
                """),
                {"talent_id": talent_id, "user_id": user_id}
            )
            existing = result.fetchone()
            
            candidate_id = str(uuid.uuid4()) if not existing else existing.id
            
            if existing:
                # Update existing
                await self.db.execute(
                    text("""
                        UPDATE candidate_profiles
                        SET name = :name, email = :email, phone = :phone, mobile = :mobile,
                            skills = :skills, certifications = :certifications,
                            work_history = :work_history, education = :education,
                            avionte_sync_at = :sync_at
                        WHERE id = :candidate_id
                    """),
                    {
                        "candidate_id": candidate_id,
                        "name": candidate.get("name"),
                        "email": candidate.get("email"),
                        "phone": candidate.get("phone"),
                        "mobile": candidate.get("mobile"),
                        "skills": json.dumps(candidate.get("skills", [])),
                        "certifications": json.dumps(candidate.get("certifications", [])),
                        "work_history": json.dumps(candidate.get("work_history", [])),
                        "education": json.dumps(candidate.get("education", [])),
                        "sync_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                action = "updated"
            else:
                # Create new
                await self.db.execute(
                    text("""
                        INSERT INTO candidate_profiles
                        (id, user_id, name, email, phone, mobile, skills, certifications,
                         work_history, education, avionte_talent_id, avionte_sync_at, created_at)
                        VALUES
                        (:id, :user_id, :name, :email, :phone, :mobile, :skills, :certifications,
                         :work_history, :education, :talent_id, :sync_at, :created_at)
                    """),
                    {
                        "id": candidate_id,
                        "user_id": user_id,
                        "name": candidate.get("name"),
                        "email": candidate.get("email"),
                        "phone": candidate.get("phone"),
                        "mobile": candidate.get("mobile"),
                        "skills": json.dumps(candidate.get("skills", [])),
                        "certifications": json.dumps(candidate.get("certifications", [])),
                        "work_history": json.dumps(candidate.get("work_history", [])),
                        "education": json.dumps(candidate.get("education", [])),
                        "talent_id": talent_id,
                        "sync_at": datetime.now(timezone.utc).isoformat(),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                action = "created"
            
            await self.db.commit()
            
            logger.info(f"Successfully synced talent {talent_id} from Avionté (action: {action})")
            
            return {
                "success": True,
                "candidate_id": candidate_id,
                "action": action
            }
            
        except AvionteException as e:
            logger.error(f"Failed to sync talent {talent_id} from Avionté: {str(e)}")
            await self.db.rollback()
            raise
