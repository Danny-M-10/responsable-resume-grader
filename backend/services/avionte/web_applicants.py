"""
Avionté Web Applicants API endpoints
"""
import logging
from typing import Optional, List, Dict, Any
from .client import AvionteClient
from .exceptions import AvionteException

logger = logging.getLogger(__name__)


class AvionteWebApplicantsAPI:
    """Web Applicants management API"""
    
    def __init__(self, client: AvionteClient):
        """
        Initialize Web Applicants API
        
        Args:
            client: Avionté API client instance
        """
        self.client = client
    
    async def get_web_applicants_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all web applicants for a specific job
        
        Args:
            job_id: Job ID
            
        Returns:
            List of web applicants
        """
        endpoint = f"/v2/webApplicant/job/{job_id}"
        try:
            response = await self.client.get(endpoint)
            # Response might be a list or wrapped in a property
            if isinstance(response, list):
                return response
            elif isinstance(response, dict):
                return response.get("webApplicants", response.get("applicants", []))
            return []
        except AvionteException as e:
            logger.error(f"Failed to get web applicants for job {job_id}: {str(e)}")
            raise
    
    async def get_web_applicant(self, applicant_id: str) -> Dict[str, Any]:
        """
        Get details of a specific web applicant
        
        Args:
            applicant_id: Web applicant ID
            
        Returns:
            Web applicant data
        """
        endpoint = f"/v2/webApplicant/{applicant_id}"
        return await self.client.get(endpoint)
    
    async def query_web_applicants(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Query multiple web applicants
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Query results with pagination
        """
        endpoint = "/v2/webApplicant/query"
        params = {
            "page": page,
            "pageSize": page_size
        }
        json_data = {"filters": filters or {}}
        return await self.client.post(endpoint, json_data=json_data, params=params)
    
    async def get_web_applications_for_talent(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get web applications for a specific talent
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of web applications
        """
        endpoint = f"/v2/webApplicant/talent/{talent_id}"
        try:
            response = await self.client.get(endpoint)
            if isinstance(response, list):
                return response
            elif isinstance(response, dict):
                return response.get("webApplications", response.get("applications", []))
            return []
        except AvionteException as e:
            logger.error(f"Failed to get web applications for talent {talent_id}: {str(e)}")
            raise
