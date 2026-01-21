"""
Avionté Companies API endpoints
"""
import logging
from typing import Optional, List, Dict, Any
from .client import AvionteClient
from .models import AvionteCompany
from .exceptions import AvionteException

logger = logging.getLogger(__name__)


class AvionteCompaniesAPI:
    """Companies management API"""
    
    def __init__(self, client: AvionteClient):
        """
        Initialize Companies API
        
        Args:
            client: Avionté API client instance
        """
        self.client = client
    
    async def create_company(self, company: AvionteCompany) -> Dict[str, Any]:
        """
        Create a new company
        
        Args:
            company: Company data
            
        Returns:
            Created company data with companyId
        """
        endpoint = "/v2/company"
        data = company.model_dump(exclude_none=True, exclude={"companyId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Get a company by ID
        
        Args:
            company_id: Company ID
            
        Returns:
            Company data
        """
        endpoint = f"/v2/company/{company_id}"
        return await self.client.get(endpoint)
    
    async def update_company(self, company_id: str, company: AvionteCompany) -> Dict[str, Any]:
        """
        Update a company
        
        Args:
            company_id: Company ID
            company: Updated company data
            
        Returns:
            Updated company data
        """
        endpoint = f"/v2/company/{company_id}"
        data = company.model_dump(exclude_none=True, exclude={"companyId"})
        return await self.client.put(endpoint, json_data=data)
    
    async def query_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Query multiple companies
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Query results with pagination
        """
        endpoint = "/v2/company/query"
        params = {
            "page": page,
            "pageSize": page_size
        }
        json_data = {"filters": filters or {}}
        return await self.client.post(endpoint, json_data=json_data, params=params)
    
    async def get_company_ids(self) -> List[str]:
        """
        Get all company IDs
        
        Returns:
            List of company IDs
        """
        endpoint = "/v2/company/ids"
        response = await self.client.get(endpoint)
        return response.get("companyIds", [])
    
    # Company Tags
    async def add_company_tag(self, company_id: str, tag: str) -> Dict[str, Any]:
        """
        Add a tag to a company
        
        Args:
            company_id: Company ID
            tag: Tag name
            
        Returns:
            Response data
        """
        endpoint = f"/v2/company/{company_id}/tag"
        data = {"tag": tag}
        return await self.client.post(endpoint, json_data=data)
    
    async def remove_company_tag(self, company_id: str, tag: str) -> None:
        """
        Remove a tag from a company
        
        Args:
            company_id: Company ID
            tag: Tag name
        """
        endpoint = f"/v2/company/{company_id}/tag/{tag}"
        await self.client.delete(endpoint)
    
    async def get_company_tags(self, company_id: str) -> List[str]:
        """
        Get tags for a company
        
        Args:
            company_id: Company ID
            
        Returns:
            List of tags
        """
        endpoint = f"/v2/company/{company_id}/tag"
        response = await self.client.get(endpoint)
        return response.get("tags", [])
    
    # Company Restrictions
    async def add_restriction(
        self,
        company_id: str,
        talent_id: str,
        restriction_type: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a restriction for a company
        
        Args:
            company_id: Company ID
            talent_id: Talent ID
            restriction_type: Type of restriction
            reason: Optional reason
            
        Returns:
            Response data
        """
        endpoint = f"/v2/company/{company_id}/restriction"
        data = {
            "talentId": talent_id,
            "restrictionType": restriction_type,
            "reason": reason
        }
        return await self.client.post(endpoint, json_data=data)
    
    async def get_restrictions(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Get restrictions for a company
        
        Args:
            company_id: Company ID
            
        Returns:
            List of restrictions
        """
        endpoint = f"/v2/company/{company_id}/restriction"
        response = await self.client.get(endpoint)
        return response.get("restrictions", [])
