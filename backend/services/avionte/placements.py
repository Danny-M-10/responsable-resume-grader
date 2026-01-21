"""
Avionté Placements API endpoints
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from .client import AvionteClient
from .models import AviontePlacement
from .exceptions import AvionteException

logger = logging.getLogger(__name__)


class AviontePlacementsAPI:
    """Placements management API"""
    
    def __init__(self, client: AvionteClient):
        """
        Initialize Placements API
        
        Args:
            client: Avionté API client instance
        """
        self.client = client
    
    async def create_placement(self, placement: AviontePlacement) -> Dict[str, Any]:
        """
        Create a new placement
        
        Args:
            placement: Placement data
            
        Returns:
            Created placement data with placementId
        """
        endpoint = "/v2/placement"
        data = placement.model_dump(exclude_none=True, exclude={"placementId"})
        return await self.client.post(endpoint, json_data=data)
    
    async def get_placement(self, placement_id: str) -> Dict[str, Any]:
        """
        Get a placement by ID
        
        Args:
            placement_id: Placement ID
            
        Returns:
            Placement data
        """
        endpoint = f"/v2/placement/{placement_id}"
        return await self.client.get(endpoint)
    
    async def get_extended_placement(self, placement_id: str) -> Dict[str, Any]:
        """
        Get extended placement details
        
        Args:
            placement_id: Placement ID
            
        Returns:
            Extended placement data
        """
        endpoint = f"/v2/placement/{placement_id}/extended"
        return await self.client.get(endpoint)
    
    async def update_placement(self, placement_id: str, placement: AviontePlacement) -> Dict[str, Any]:
        """
        Update a placement
        
        Args:
            placement_id: Placement ID
            placement: Updated placement data
            
        Returns:
            Updated placement data
        """
        endpoint = f"/v2/placement/{placement_id}"
        data = placement.model_dump(exclude_none=True, exclude={"placementId"})
        return await self.client.put(endpoint, json_data=data)
    
    async def query_placements(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Query multiple placements
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Query results with pagination
        """
        endpoint = "/v2/placement/query"
        params = {
            "page": page,
            "pageSize": page_size
        }
        json_data = {"filters": filters or {}}
        return await self.client.post(endpoint, json_data=json_data, params=params)
    
    async def get_placement_ids(self) -> List[str]:
        """
        Get all placement IDs
        
        Returns:
            List of placement IDs
        """
        endpoint = "/v2/placement/ids"
        response = await self.client.get(endpoint)
        return response.get("placementIds", [])
    
    async def get_active_placements(
        self,
        company_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active placements, optionally filtered by company IDs
        
        Args:
            company_ids: Optional list of company IDs to filter by
            
        Returns:
            List of active placements
        """
        endpoint = "/v2/placement/active"
        json_data = {}
        if company_ids:
            json_data["companyIds"] = company_ids
        response = await self.client.post(endpoint, json_data=json_data)
        return response.get("placements", [])
    
    async def get_placement_schedules(self, placement_id: str) -> List[Dict[str, Any]]:
        """
        Get schedules for a placement
        
        Args:
            placement_id: Placement ID
            
        Returns:
            List of placement schedules
        """
        endpoint = f"/v2/placement/{placement_id}/schedule"
        response = await self.client.get(endpoint)
        return response.get("schedules", [])
    
    async def cancel_placement_schedules(
        self,
        placement_id: str,
        schedule_ids: List[str],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel placement schedule shifts
        
        Args:
            placement_id: Placement ID
            schedule_ids: List of schedule IDs to cancel
            reason: Optional cancellation reason
            
        Returns:
            Response data
        """
        endpoint = f"/v2/placement/{placement_id}/schedule/cancel"
        data = {
            "scheduleIds": schedule_ids,
            "reason": reason
        }
        return await self.client.post(endpoint, json_data=data)
    
    async def get_end_reasons(self) -> List[Dict[str, Any]]:
        """
        Get placement end reason definitions
        
        Returns:
            List of end reason definitions
        """
        endpoint = "/v2/placement/endReason"
        response = await self.client.get(endpoint)
        return response.get("endReasons", [])
