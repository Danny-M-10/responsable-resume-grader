"""
Avionté Talent API endpoints
"""
import logging
from typing import Optional, List, Dict, Any
from .client import AvionteClient
from .models import AvionteTalent, AvionteCertification, AvionteSkill, AvionteWorkHistory, AvionteEducation, AvionteDocument
from .exceptions import AvionteException

logger = logging.getLogger(__name__)


class AvionteTalentAPI:
    """Talent management API"""
    
    def __init__(self, client: AvionteClient):
        """
        Initialize Talent API
        
        Args:
            client: Avionté API client instance
        """
        self.client = client
    
    async def create_talent(self, talent: AvionteTalent) -> Dict[str, Any]:
        """
        Create a new talent
        
        Args:
            talent: Talent data
            
        Returns:
            Created talent data with talentId
        """
        endpoint = "/v2/talent"
        data = talent.model_dump(exclude_none=True, exclude={"talentId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def get_talent(self, talent_id: str) -> Dict[str, Any]:
        """
        Get a talent by ID
        
        Args:
            talent_id: Talent ID
            
        Returns:
            Talent data
        """
        endpoint = f"/v2/talent/{talent_id}"
        return await self.client.get(endpoint)
    
    async def update_talent(self, talent_id: str, talent: AvionteTalent) -> Dict[str, Any]:
        """
        Update a talent
        
        Args:
            talent_id: Talent ID
            talent: Updated talent data
            
        Returns:
            Updated talent data
        """
        endpoint = f"/v2/talent/{talent_id}"
        data = talent.model_dump(exclude_none=True, exclude={"talentId"})
        return await self.client.put(endpoint, json_data=data)
    
    async def query_talents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Query multiple talents
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Query results with pagination
        """
        endpoint = "/v2/talent/query"
        params = {
            "page": page,
            "pageSize": page_size
        }
        json_data = {"filters": filters or {}}
        return await self.client.post(endpoint, json_data=json_data, params=params)
    
    async def get_talent_ids(self, modified_since: Optional[str] = None) -> List[str]:
        """
        Get talent IDs, optionally filtered by modified date
        
        Args:
            modified_since: ISO date string for filtering
            
        Returns:
            List of talent IDs
        """
        endpoint = "/v2/talent/ids"
        params = {}
        if modified_since:
            params["modifiedSince"] = modified_since
        response = await self.client.get(endpoint, params=params)
        return response.get("talentIds", [])
    
    # Certifications
    async def add_certification(self, talent_id: str, certification: AvionteCertification) -> Dict[str, Any]:
        """
        Add a certification to a talent
        
        Args:
            talent_id: Talent ID
            certification: Certification data
            
        Returns:
            Created certification data
        """
        endpoint = f"/v2/talent/{talent_id}/certification"
        data = certification.model_dump(exclude_none=True, exclude={"certificationId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def remove_certification(self, talent_id: str, certification_id: str) -> None:
        """
        Remove a certification from a talent
        
        Args:
            talent_id: Talent ID
            certification_id: Certification ID
        """
        endpoint = f"/v2/talent/{talent_id}/certification/{certification_id}"
        await self.client.delete(endpoint)
    
    async def get_certifications(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get certifications for a talent
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of certifications
        """
        endpoint = f"/v2/talent/{talent_id}/certification"
        response = await self.client.get(endpoint)
        return response.get("certifications", [])
    
    # Skills
    async def add_skills(self, talent_id: str, skills: List[AvionteSkill]) -> Dict[str, Any]:
        """
        Add skills to a talent
        
        Args:
            talent_id: Talent ID
            skills: List of skills
            
        Returns:
            Response data
        """
        endpoint = f"/v2/talent/{talent_id}/skill"
        data = {"skills": [skill.model_dump(exclude_none=True) for skill in skills]}
        return await self.client.post(endpoint, json_data=data)
    
    async def get_skills(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get skills for a talent
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of skills
        """
        endpoint = f"/v2/talent/{talent_id}/skill"
        response = await self.client.get(endpoint)
        return response.get("skills", [])
    
    async def remove_skills(self, talent_id: str, skill_ids: List[str]) -> None:
        """
        Remove skills from a talent
        
        Args:
            talent_id: Talent ID
            skill_ids: List of skill IDs to remove
        """
        endpoint = f"/v2/talent/{talent_id}/skill"
        data = {"skillIds": skill_ids}
        await self.client.post(endpoint, json_data=data)  # Note: API may use DELETE, adjust if needed
    
    # Work History
    async def add_work_history(self, talent_id: str, work_history: AvionteWorkHistory) -> Dict[str, Any]:
        """
        Add work history to a talent
        
        Args:
            talent_id: Talent ID
            work_history: Work history data
            
        Returns:
            Created work history data
        """
        endpoint = f"/v2/talent/{talent_id}/workHistory"
        data = work_history.model_dump(exclude_none=True, exclude={"workHistoryId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def get_work_history(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get work history for a talent
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of work history entries
        """
        endpoint = f"/v2/talent/{talent_id}/workHistory"
        response = await self.client.get(endpoint)
        return response.get("workHistory", [])
    
    async def update_work_history(
        self,
        talent_id: str,
        work_history_id: str,
        work_history: AvionteWorkHistory
    ) -> Dict[str, Any]:
        """
        Update work history
        
        Args:
            talent_id: Talent ID
            work_history_id: Work history ID
            work_history: Updated work history data
            
        Returns:
            Updated work history data
        """
        endpoint = f"/v2/talent/{talent_id}/workHistory/{work_history_id}"
        data = work_history.model_dump(exclude_none=True, exclude={"workHistoryId"})
        return await self.client.put(endpoint, json_data=data)
    
    # Education
    async def add_education(self, talent_id: str, education: AvionteEducation) -> Dict[str, Any]:
        """
        Add education to a talent
        
        Args:
            talent_id: Talent ID
            education: Education data
            
        Returns:
            Created education data
        """
        endpoint = f"/v2/talent/{talent_id}/education"
        data = education.model_dump(exclude_none=True, exclude={"educationId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def get_education(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get education for a talent
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of education entries
        """
        endpoint = f"/v2/talent/{talent_id}/education"
        response = await self.client.get(endpoint)
        return response.get("education", [])
    
    # Documents
    async def upload_document(
        self,
        talent_id: str,
        file_data: bytes,
        file_name: str,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a document for a talent
        
        Args:
            talent_id: Talent ID
            file_data: File binary data
            file_name: File name
            document_type: Document type identifier
            
        Returns:
            Uploaded document data
        """
        endpoint = f"/v2/talent/{talent_id}/document"
        # Note: Actual implementation may require multipart/form-data
        # This is a simplified version - adjust based on actual API requirements
        import base64
        data = {
            "fileName": file_name,
            "fileData": base64.b64encode(file_data).decode("utf-8"),
            "documentType": document_type
        }
        return await self.client.post(endpoint, json_data=data)
    
    async def get_documents(self, talent_id: str) -> List[Dict[str, Any]]:
        """
        Get documents for a talent
        
        Args:
            talent_id: Talent ID
            
        Returns:
            List of documents
        """
        endpoint = f"/v2/talent/{talent_id}/document"
        response = await self.client.get(endpoint)
        return response.get("documents", [])
