"""
Avionté Jobs API endpoints
"""
import logging
from typing import Optional, List, Dict, Any
from .client import AvionteClient
from .models import AvionteJob, AvionteJobSkill, AvionteJobCertification
from .exceptions import AvionteException

logger = logging.getLogger(__name__)


class AvionteJobsAPI:
    """Jobs management API"""
    
    def __init__(self, client: AvionteClient):
        """
        Initialize Jobs API
        
        Args:
            client: Avionté API client instance
        """
        self.client = client
    
    async def create_job(self, job: AvionteJob) -> Dict[str, Any]:
        """
        Create a new job
        
        Args:
            job: Job data
            
        Returns:
            Created job data with jobId
        """
        endpoint = "/v2/job"
        data = job.model_dump(exclude_none=True, exclude={"jobId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get a job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job data
        """
        endpoint = f"/v2/job/{job_id}"
        return await self.client.get(endpoint)
    
    async def update_job(self, job_id: str, job: AvionteJob) -> Dict[str, Any]:
        """
        Update a job
        
        Args:
            job_id: Job ID
            job: Updated job data
            
        Returns:
            Updated job data
        """
        endpoint = f"/v2/job/{job_id}"
        data = job.model_dump(exclude_none=True, exclude={"jobId"})
        return await self.client.put(endpoint, json_data=data)
    
    async def query_jobs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Query multiple jobs
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Query results with pagination
        """
        endpoint = "/v2/job/query"
        params = {
            "page": page,
            "pageSize": page_size
        }
        json_data = {"filters": filters or {}}
        return await self.client.post(endpoint, json_data=json_data, params=params)
    
    async def get_job_ids(self) -> List[str]:
        """
        Get all job IDs
        
        Returns:
            List of job IDs
        """
        endpoint = "/v2/job/ids"
        response = await self.client.get(endpoint)
        return response.get("jobIds", [])
    
    async def get_matching_jobs(
        self,
        talent_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get jobs matching a talent
        
        Args:
            talent_id: Talent ID
            filters: Additional filter criteria
            
        Returns:
            List of matching jobs
        """
        endpoint = "/v2/job/match"
        json_data = {
            "talentId": talent_id,
            "filters": filters or {}
        }
        response = await self.client.post(endpoint, json_data=json_data)
        return response.get("jobs", [])
    
    # Job Skills
    async def add_job_skills(self, job_id: str, skills: List[AvionteJobSkill]) -> Dict[str, Any]:
        """
        Add skills to a job
        
        Args:
            job_id: Job ID
            skills: List of job skills
            
        Returns:
            Response data
        """
        endpoint = f"/v2/job/{job_id}/skill"
        data = {"skills": [skill.model_dump(exclude_none=True) for skill in skills]}
        return await self.client.post(endpoint, json_data=data)
    
    async def get_job_skills(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get skills for a job
        
        Args:
            job_id: Job ID
            
        Returns:
            List of job skills
        """
        endpoint = f"/v2/job/{job_id}/skill"
        response = await self.client.get(endpoint)
        return response.get("skills", [])
    
    async def remove_job_skills(self, job_id: str, skill_ids: List[str]) -> None:
        """
        Remove skills from a job
        
        Args:
            job_id: Job ID
            skill_ids: List of skill IDs to remove
        """
        endpoint = f"/v2/job/{job_id}/skill"
        data = {"skillIds": skill_ids}
        await self.client.post(endpoint, json_data=data)  # Note: API may use DELETE, adjust if needed
    
    # Job Documents
    async def upload_job_document(
        self,
        job_id: str,
        file_data: bytes,
        file_name: str
    ) -> Dict[str, Any]:
        """
        Upload a document for a job
        
        Args:
            job_id: Job ID
            file_data: File binary data
            file_name: File name
            
        Returns:
            Uploaded document data
        """
        endpoint = f"/v2/job/{job_id}/document"
        # Note: Actual implementation may require multipart/form-data
        import base64
        data = {
            "fileName": file_name,
            "fileData": base64.b64encode(file_data).decode("utf-8")
        }
        return await self.client.post(endpoint, json_data=data)
    
    # VMS Jobs
    async def create_vms_job(self, job: AvionteJob, vms_id: str) -> Dict[str, Any]:
        """
        Create a VMS job
        
        Args:
            job: Job data
            vms_id: VMS identifier
            
        Returns:
            Created VMS job data
        """
        endpoint = "/v2/job/vms"
        data = job.model_dump(exclude_none=True, exclude={"jobId"})
        data["vmsId"] = vms_id
        return await self.client.post(endpoint, json_data=data)
    
    async def update_vms_job(self, job_id: str, job: AvionteJob) -> Dict[str, Any]:
        """
        Update a VMS job
        
        Args:
            job_id: Job ID
            job: Updated job data
            
        Returns:
            Updated job data
        """
        endpoint = f"/v2/job/vms/{job_id}"
        data = job.model_dump(exclude_none=True, exclude={"jobId"})
        return await self.client.put(endpoint, json_data=data)
    
    async def patch_vms_job(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Partially update a VMS job
        
        Args:
            job_id: Job ID
            updates: Partial update data
            
        Returns:
            Updated job data
        """
        endpoint = f"/v2/job/vms/{job_id}"
        return await self.client.patch(endpoint, json_data=updates)
    
    async def get_vms_jobs(self, vms_id: str) -> List[Dict[str, Any]]:
        """
        Get VMS jobs by VMS ID
        
        Args:
            vms_id: VMS identifier
            
        Returns:
            List of VMS jobs
        """
        endpoint = f"/v2/job/vms/{vms_id}"
        response = await self.client.get(endpoint)
        return response.get("jobs", [])
    
    # Job Status
    async def get_job_statuses(self) -> List[Dict[str, Any]]:
        """
        Get available job status definitions
        
        Returns:
            List of job status definitions
        """
        endpoint = "/v2/job/status"
        response = await self.client.get(endpoint)
        return response.get("statuses", [])
    
    # Placements for Job
    async def get_placements(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get placements for a job
        
        Args:
            job_id: Job ID
            
        Returns:
            List of placements
        """
        endpoint = f"/v2/job/{job_id}/placement"
        response = await self.client.get(endpoint)
        return response.get("placements", [])
